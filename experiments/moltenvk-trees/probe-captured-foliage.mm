// Captured packed-foliage inputs with synthetic depth. No original-depth claim.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include "foliage-cull-hiz-workaround.h"

static NSData *readInput(NSString *root, NSString *name) {
    NSData *data = [NSData dataWithContentsOfFile:[root stringByAppendingPathComponent:name]];
    if (!data) { fprintf(stderr,"Missing input %s\n",name.UTF8String); exit(3); }
    return data;
}

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2 && argc != 3) return 2;
        bool bypass = argc == 3 && std::strcmp(argv[2], "--bypass-hiz") == 0;
        if (argc == 3 && !bypass) return 2;
        NSString *root = [NSString stringWithUTF8String:argv[1]];
        NSString *source = [[NSString alloc] initWithData:readInput(root,@"foliage-cull.metal") encoding:NSUTF8StringEncoding];
        std::string original = source.UTF8String, changed = original + "\n// modified\n";
        if (rdr2BypassCapturedFoliageHiZ(changed) || changed != original + "\n// modified\n") return 11;
        changed = "kernel void unrelated() {}\n";
        if (rdr2BypassCapturedFoliageHiZ(changed) || changed != "kernel void unrelated() {}\n") return 12;
        setenv("RDR2_MVK_FOLIAGE_HIZ_BYPASS", "0", 1);
        changed = original;
        if (rdr2BypassCapturedFoliageHiZ(changed) || changed != original) return 13;
        unsetenv("RDR2_MVK_FOLIAGE_HIZ_BYPASS");
        if (bypass) {
            changed = original;
            if (!rdr2BypassCapturedFoliageHiZ(changed)) return 10;
            source = [NSString stringWithUTF8String:changed.c_str()];
        }
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) return 4;
        id<MTLCommandQueue> queue = [device newCommandQueue];
        NSArray *cases = @[
            @{@"name":@"hiz-disabled-fast",@"hiz":@NO,@"depth":@0,@"fast":@YES},
            @{@"name":@"clear-depth-fast",@"hiz":@YES,@"depth":@0,@"fast":@YES},
            @{@"name":@"depth-300-fast",@"hiz":@YES,@"depth":@300,@"fast":@YES},
            @{@"name":@"depth-10000-fast",@"hiz":@YES,@"depth":@10000,@"fast":@YES},
            @{@"name":@"hiz-disabled-precise",@"hiz":@NO,@"depth":@0,@"fast":@NO},
            @{@"name":@"depth-300-precise",@"hiz":@YES,@"depth":@300,@"fast":@NO}
        ];
        NSMutableDictionary *pipelines = [NSMutableDictionary new], *functions = [NSMutableDictionary new];
        NSMutableArray *results = [NSMutableArray new];
        NSArray *reference = nil;
        for (NSDictionary *test in cases) {
            NSNumber *fast = test[@"fast"];
            id<MTLFunction> function = functions[fast];
            id<MTLComputePipelineState> pipeline = pipelines[fast];
            NSError *error = nil;
            if (!pipeline) {
                MTLCompileOptions *options = [MTLCompileOptions new];
                options.fastMathEnabled = fast.boolValue;
                id<MTLLibrary> library = [device newLibraryWithSource:source options:options error:&error];
                if (!library) { fprintf(stderr,"%s\n",error.localizedDescription.UTF8String); return 5; }
                function = [library newFunctionWithName:@"VkMain"];
                pipeline = [device newComputePipelineStateWithFunction:function error:&error];
                if (!pipeline) { fprintf(stderr,"%s\n",error.localizedDescription.UTF8String); return 6; }
                functions[fast] = function; pipelines[fast] = pipeline;
            }
            NSMutableDictionary *inputs = [NSMutableDictionary new];
            for (NSString *name in @[@"camera",@"wind",@"aux",@"globals",@"clump",@"lod",@"object",@"transforms",@"extra",@"args"]) {
                NSData *data = readInput(root,[NSString stringWithFormat:@"foliage-cull-%@.bin",name]);
                inputs[name] = [device newBufferWithBytes:data.bytes length:data.length options:MTLResourceStorageModeShared];
            }
            id<MTLBuffer> globals = inputs[@"globals"], args = inputs[@"args"];
            if (globals.length != 928 || args.length != 100 || ((id<MTLBuffer>)inputs[@"transforms"]).length != 2208) return 14;
            ((uint32_t *)globals.contents)[376/4] = [test[@"hiz"] boolValue] ? 1 : 0;
            for (NSUInteger n=0;n<5;++n) ((uint32_t *)args.contents)[n*5+1] = 0;
            uint32_t sizes[] = {0,192,552,552,552,552,100,0,132,2208,3000};
            id<MTLBuffer> sizeBuffer = [device newBufferWithBytes:sizes length:sizeof(sizes) options:MTLResourceStorageModeShared];
            NSMutableArray *lists = [NSMutableArray new];
            for (NSUInteger n=0;n<4;++n) {
                id<MTLBuffer> list = [device newBufferWithLength:552 options:MTLResourceStorageModeShared];
                memset(list.contents,0,list.length); [lists addObject:list];
            }
            MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR32Float width:128 height:72 mipmapped:YES];
            td.mipmapLevelCount = 7;
            td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead;
            id<MTLTexture> texture = [device newTextureWithDescriptor:td];
            for (NSUInteger mip=0;mip<texture.mipmapLevelCount;++mip) {
                NSUInteger w=MAX(1ul,texture.width>>mip),h=MAX(1ul,texture.height>>mip);
                NSMutableData *pixels = [NSMutableData dataWithLength:w*h*sizeof(float)];
                float *values = (float *)pixels.mutableBytes;
                for (NSUInteger n=0;n<w*h;++n) values[n] = [test[@"depth"] floatValue];
                [texture replaceRegion:MTLRegionMake2D(0,0,w,h) mipmapLevel:mip withBytes:values bytesPerRow:w*sizeof(float)];
            }
            id<MTLArgumentEncoder> e0 = [function newArgumentEncoderWithBufferIndex:0], e1 = [function newArgumentEncoderWithBufferIndex:1];
            id<MTLBuffer> set0 = [device newBufferWithLength:e0.encodedLength options:MTLResourceStorageModeShared];
            id<MTLBuffer> set1 = [device newBufferWithLength:e1.encodedLength options:MTLResourceStorageModeShared];
            [e0 setArgumentBuffer:set0 offset:0]; [e1 setArgumentBuffer:set1 offset:0];
            [e0 setBuffer:sizeBuffer offset:0 atIndex:0];
            NSArray *ds0 = @[@"camera",@"wind",@"aux",@"globals",@"clump"];
            for (NSUInteger n=0;n<ds0.count;++n) [e0 setBuffer:inputs[ds0[n]] offset:0 atIndex:n+1];
            [e1 setBuffer:sizeBuffer offset:0 atIndex:0]; [e1 setBuffer:inputs[@"lod"] offset:0 atIndex:1];
            for (NSUInteger n=0;n<4;++n) [e1 setBuffer:lists[n] offset:0 atIndex:n+2];
            [e1 setBuffer:args offset:0 atIndex:6]; [e1 setTexture:texture atIndex:7];
            [e1 setBuffer:inputs[@"object"] offset:0 atIndex:8];
            [e1 setBuffer:inputs[@"transforms"] offset:0 atIndex:9];
            [e1 setBuffer:inputs[@"extra"] offset:0 atIndex:10];
            id<MTLCommandBuffer> cb = [queue commandBuffer];
            id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
            [enc setComputePipelineState:pipeline]; [enc setBuffer:set0 offset:0 atIndex:0];
            [enc setBuffer:set1 offset:0 atIndex:1]; [enc setBuffer:sizeBuffer offset:0 atIndex:29];
            for (id<MTLBuffer> b in inputs.allValues) [enc useResource:b usage:MTLResourceUsageRead|MTLResourceUsageWrite];
            for (id<MTLBuffer> b in lists) [enc useResource:b usage:MTLResourceUsageRead|MTLResourceUsageWrite];
            [enc useResource:sizeBuffer usage:MTLResourceUsageRead]; [enc useResource:texture usage:MTLResourceUsageRead];
            [enc dispatchThreadgroups:MTLSizeMake(3,1,1) threadsPerThreadgroup:MTLSizeMake(64,1,1)];
            [enc endEncoding]; [cb commit]; [cb waitUntilCompleted];
            if (cb.status != MTLCommandBufferStatusCompleted) { fprintf(stderr,"%s\n",cb.error.localizedDescription.UTF8String); return 7; }
            NSMutableArray *counts = [NSMutableArray new], *selected = [NSMutableArray new];
            for (NSUInteger n=0;n<5;++n) [counts addObject:@(((uint32_t *)args.contents)[n*5+1])];
            NSUInteger count = ((uint32_t *)args.contents)[1];
            if (count>138) return 8;
            for (NSUInteger n=0;n<count;++n) [selected addObject:@(((uint32_t *)((id<MTLBuffer>)lists[0]).contents)[n]&65535u)];
            [selected sortUsingSelector:@selector(compare:)];
            if (!reference) reference = [selected copy];
            if (bypass && ![selected isEqualToArray:reference]) return 15;
            [results addObject:@{@"case":test,@"instance_counts":counts,@"selected_ids":selected}];
            printf("%s: %s\n",[test[@"name"] UTF8String],selected.description.UTF8String); fflush(stdout);
        }
        NSDictionary *report = @{@"gpu":device.name,@"synthetic_depth_controls":@YES,@"game_hiz_data_reproduced":@NO,@"hiz_bypass":@(bypass),@"hiz_mip_levels":@7,@"guard_negative_controls_passed":@YES,@"results":results};
        NSData *json = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:nil];
        if (!json || ![json writeToFile:[root stringByAppendingPathComponent:bypass ? @"isolated-foliage-bypass.json" : @"isolated-foliage-controls.json"] options:NSDataWritingWithoutOverwriting error:nil]) return 9;
    }
    return 0;
}
