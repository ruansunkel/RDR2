// Diagnostic controls for one captured culling shader. Uses synthetic uniform
// depth textures: this is not a reproduction of the game's actual HiZ data.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <cmath>
#include <cstring>
#include "tree-cull-hiz-workaround.h"

static NSData *readFile(NSString *root, NSString *name) {
    NSData *data = [NSData dataWithContentsOfFile:[root stringByAppendingPathComponent:name]];
    if (!data) { fprintf(stderr, "Missing input: %s\n", name.UTF8String); exit(3); }
    return data;
}

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2 && argc != 3) return 2;
        bool bypass = argc == 3 && std::strcmp(argv[2], "--bypass-hiz") == 0;
        NSString *root = [NSString stringWithUTF8String:argv[1]];
        NSString *source = [[NSString alloc] initWithData:readFile(root,@"compute-sources/cps134.metal") encoding:NSUTF8StringEncoding];
        std::string original = source.UTF8String;
        std::string changed = original;
        changed += "\n// deliberately different shader\n";
        if (rdr2BypassCapturedTreeHiZ(changed) || changed != original + "\n// deliberately different shader\n") return 11;
        changed = "kernel void unrelated() {}\n";
        if (rdr2BypassCapturedTreeHiZ(changed) || changed != "kernel void unrelated() {}\n") return 12;
        setenv("RDR2_MVK_TREE_HIZ_BYPASS", "0", 1);
        changed = original;
        if (rdr2BypassCapturedTreeHiZ(changed) || changed != original) return 13;
        unsetenv("RDR2_MVK_TREE_HIZ_BYPASS");
        if (bypass) {
            std::string edited = source.UTF8String;
            if (!rdr2BypassCapturedTreeHiZ(edited)) return 10;
            source = [NSString stringWithUTF8String:edited.c_str()];
        }
        NSString *signature = @"uint3 gl_GlobalInvocationID [[thread_position_in_grid]])";
        NSString *branch = @"if ((((_211 > 0.0) && _623) && (_208 > 0.0)) && true)";
        if (![source containsString:signature] || ![source containsString:branch]) return 4;
        source = [source stringByReplacingOccurrencesOfString:signature withString:
            @"device float* cullDebug [[buffer(28)]], uint3 gl_GlobalInvocationID [[thread_position_in_grid]])"];
        NSString *debug = @"uint di = gl_GlobalInvocationID.x * 16u;\n"
            "cullDebug[di+0] = float(_245); cullDebug[di+1] = float(_411);\n"
            "cullDebug[di+2] = float(_544); cullDebug[di+3] = float(_623);\n"
            "cullDebug[di+4] = _208; cullDebug[di+5] = _211;\n"
            "cullDebug[di+6] = _508; cullDebug[di+7] = _509.x;\n"
            "cullDebug[di+8] = _509.y; cullDebug[di+9] = _510.x;\n"
            "cullDebug[di+10] = _510.y; cullDebug[di+11] = spvDescriptorSet1.m_8.read(uint2(0), 0).x;\n"
            "cullDebug[di+12] = _193.x; cullDebug[di+13] = _193.y; cullDebug[di+14] = _193.z;\n"
            "cullDebug[di+15] = _449;\n";
        source = [source stringByReplacingOccurrencesOfString:branch withString:[debug stringByAppendingString:branch]];
        [source writeToFile:[root stringByAppendingPathComponent:@"isolated-cull-instrumented.metal"] atomically:YES encoding:NSUTF8StringEncoding error:nil];
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
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
        for (NSDictionary *test in cases) {
            NSNumber *fast = test[@"fast"];
            id<MTLComputePipelineState> pipeline = pipelines[fast];
            id<MTLFunction> function = functions[fast];
            if (!pipeline) {
                MTLCompileOptions *options = [MTLCompileOptions new];
                options.fastMathEnabled = fast.boolValue;
                NSError *error = nil;
                id<MTLLibrary> library = [device newLibraryWithSource:source options:options error:&error];
                if (!library) { fprintf(stderr,"%s\n",error.localizedDescription.UTF8String); return 5; }
                function = [library newFunctionWithName:@"VkMain"];
                pipeline = [device newComputePipelineStateWithFunction:function error:&error];
                if (!pipeline) { fprintf(stderr,"%s\n",error.localizedDescription.UTF8String); return 6; }
                functions[fast] = function; pipelines[fast] = pipeline;
            }
            NSMutableDictionary *inputs = [NSMutableDictionary new];
            for (NSString *name in @[@"camera",@"globals",@"aux",@"object",@"transforms",@"args"]) {
                NSData *data = readFile(root,[NSString stringWithFormat:@"tree-cull-%@.bin",name]);
                inputs[name] = [device newBufferWithBytes:data.bytes length:data.length options:MTLResourceStorageModeShared];
            }
            id<MTLBuffer> globals = inputs[@"globals"];
            ((uint32_t *)globals.contents)[376/4] = [test[@"hiz"] boolValue] ? 1 : 0;
            id<MTLBuffer> arguments = inputs[@"args"];
            for (NSUInteger n=0; n<arguments.length/20; ++n) ((uint32_t *)arguments.contents)[n*5+1] = 0;
            uint32_t sizes[] = {0,40,40,4,4,40,320,0,132,640};
            id<MTLBuffer> sizeBuffer = [device newBufferWithBytes:sizes length:sizeof(sizes) options:MTLResourceStorageModeShared];
            NSMutableArray *lists = [NSMutableArray new];
            for (NSUInteger n=0; n<5; ++n) {
                id<MTLBuffer> buffer = [device newBufferWithLength:(n==2 || n==3) ? 4 : 40 options:MTLResourceStorageModeShared];
                memset(buffer.contents,0,buffer.length); [lists addObject:buffer];
            }
            MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR32Float width:128 height:72 mipmapped:YES];
            td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead;
            id<MTLTexture> texture = [device newTextureWithDescriptor:td];
            for (NSUInteger mip=0; mip<texture.mipmapLevelCount; ++mip) {
                NSUInteger w=MAX(1ul,texture.width>>mip), h=MAX(1ul,texture.height>>mip);
                NSMutableData *pixels = [NSMutableData dataWithLength:w*h*4];
                float *values=(float *)pixels.mutableBytes;
                for (NSUInteger n=0;n<w*h;++n) values[n]=[test[@"depth"] floatValue];
                [texture replaceRegion:MTLRegionMake2D(0,0,w,h) mipmapLevel:mip withBytes:values bytesPerRow:w*4];
            }
            id<MTLArgumentEncoder> e0=[function newArgumentEncoderWithBufferIndex:0], e1=[function newArgumentEncoderWithBufferIndex:1];
            id<MTLBuffer> set0=[device newBufferWithLength:e0.encodedLength options:MTLResourceStorageModeShared];
            id<MTLBuffer> set1=[device newBufferWithLength:e1.encodedLength options:MTLResourceStorageModeShared];
            [e0 setArgumentBuffer:set0 offset:0]; [e1 setArgumentBuffer:set1 offset:0];
            [e0 setBuffer:sizeBuffer offset:0 atIndex:0];
            [e0 setBuffer:inputs[@"camera"] offset:0 atIndex:1];
            [e0 setBuffer:globals offset:0 atIndex:2];
            [e0 setBuffer:inputs[@"aux"] offset:0 atIndex:3];
            [e1 setBuffer:sizeBuffer offset:0 atIndex:0];
            for (NSUInteger n=0;n<5;++n) [e1 setBuffer:lists[n] offset:0 atIndex:n+1];
            [e1 setBuffer:arguments offset:0 atIndex:6]; [e1 setTexture:texture atIndex:7];
            [e1 setBuffer:inputs[@"object"] offset:0 atIndex:8];
            [e1 setBuffer:inputs[@"transforms"] offset:0 atIndex:9];
            id<MTLBuffer> debugBuffer=[device newBufferWithLength:64*16*4 options:MTLResourceStorageModeShared];
            memset(debugBuffer.contents,0,debugBuffer.length);
            id<MTLCommandBuffer> cb=[queue commandBuffer];
            id<MTLComputeCommandEncoder> enc=[cb computeCommandEncoder];
            [enc setComputePipelineState:pipeline]; [enc setBuffer:set0 offset:0 atIndex:0];
            [enc setBuffer:set1 offset:0 atIndex:1]; [enc setBuffer:debugBuffer offset:0 atIndex:28];
            [enc setBuffer:sizeBuffer offset:0 atIndex:29];
            for (id<MTLBuffer> buffer in inputs.allValues) [enc useResource:buffer usage:MTLResourceUsageRead|MTLResourceUsageWrite];
            for (id<MTLBuffer> buffer in lists) [enc useResource:buffer usage:MTLResourceUsageRead|MTLResourceUsageWrite];
            [enc useResource:sizeBuffer usage:MTLResourceUsageRead]; [enc useResource:texture usage:MTLResourceUsageRead];
            [enc dispatchThreadgroups:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(64,1,1)];
            [enc endEncoding]; [cb commit]; [cb waitUntilCompleted];
            if (cb.status==MTLCommandBufferStatusError) { fprintf(stderr,"%s\n",cb.error.localizedDescription.UTF8String); return 7; }
            NSMutableArray *counts=[NSMutableArray new], *ids=[NSMutableArray new], *debugRows=[NSMutableArray new];
            for (NSUInteger n=0;n<16;++n) [counts addObject:@(((uint32_t *)arguments.contents)[n*5+1])];
            NSUInteger selected=((uint32_t *)arguments.contents)[10*5+1];
            if (selected>10) return 8;
            for (NSUInteger n=0;n<selected;++n) [ids addObject:@(((uint32_t *)((id<MTLBuffer>)lists[1]).contents)[n]&65535)];
            [ids sortUsingSelector:@selector(compare:)];
            for (NSUInteger instance=0;instance<10;++instance) {
                NSMutableArray *values=[NSMutableArray new];
                for (NSUInteger n=0;n<16;++n) { float f=((float *)debugBuffer.contents)[instance*16+n]; [values addObject:std::isfinite(f)?@(f):(id)[NSNull null]]; }
                [debugRows addObject:values];
            }
            [results addObject:@{@"case":test,@"instance_counts":counts,@"selected_ids":ids,@"debug_rows":debugRows}];
            printf("%s: selected instances %s\n",[test[@"name"] UTF8String],ids.description.UTF8String); fflush(stdout);
        }
        NSDictionary *report=@{@"gpu":device.name,@"synthetic_depth_controls":@YES,@"game_hiz_data_reproduced":@NO,@"hiz_bypass":@(bypass),@"guard_negative_controls_passed":@YES,@"results":results};
        NSError *error=nil;
        NSData *json=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:&error];
        if (!json || ![json writeToFile:[root stringByAppendingPathComponent:bypass ? @"isolated-cull-bypass.json" : @"isolated-cull-controls.json"] atomically:YES]) return 9;
    }
    return 0;
}
