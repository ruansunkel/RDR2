// Reconstruct read-only captured placement-heap textures on the same GPU.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <cmath>
#include <cfloat>

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
        NSString *root = [NSString stringWithUTF8String:argv[1]];
        NSData *bytes = [NSData dataWithContentsOfFile:[root stringByAppendingPathComponent:@"hiz-heap-cull.bin"]];
        NSData *placements = [NSData dataWithContentsOfFile:[root stringByAppendingPathComponent:@"hiz-placement.json"]];
        NSError *error = nil;
        NSArray *items = [NSJSONSerialization JSONObjectWithData:placements options:0 error:&error];
        if (!bytes || !items || error) return 3;
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        MTLHeapDescriptor *hd = [MTLHeapDescriptor new];
        hd.type = MTLHeapTypePlacement;
        hd.storageMode = MTLStorageModeShared;
        hd.cpuCacheMode = MTLCPUCacheModeDefaultCache;
        hd.hazardTrackingMode = MTLHazardTrackingModeTracked;
        hd.size = bytes.length;
        id<MTLHeap> heap = [device newHeapWithDescriptor:hd];
        id<MTLBuffer> parent = [heap newBufferWithLength:bytes.length options:MTLResourceStorageModeShared offset:0];
        if (!heap || !parent) return 4;
        NSMutableArray *textures = [NSMutableArray new];
        for (NSDictionary *item in items) {
            MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR32Float
                width:[item[@"width"] unsignedIntegerValue] height:[item[@"height"] unsignedIntegerValue] mipmapped:YES];
            td.mipmapLevelCount = [item[@"levels"] unsignedIntegerValue];
            td.storageMode = MTLStorageModeShared;
            td.usage = MTLTextureUsageShaderRead | MTLTextureUsageRenderTarget;
            td.allowGPUOptimizedContents = YES;
            id<MTLTexture> texture = [heap newTextureWithDescriptor:td offset:[item[@"offset"] unsignedIntegerValue]];
            if (!texture) return 5;
            [textures addObject:texture];
        }
        memcpy(parent.contents, bytes.bytes, bytes.length);
        id<MTLCommandQueue> queue = [device newCommandQueue];
        NSMutableArray *results = [NSMutableArray new];
        for (NSUInteger i = 0; i < textures.count; ++i) {
            id<MTLTexture> texture = textures[i];
            NSDictionary *item = items[i];
            NSMutableArray *levels = [NSMutableArray new];
            for (NSUInteger mip = 0; mip < texture.mipmapLevelCount; ++mip) {
                NSUInteger w = MAX(1ul, texture.width >> mip), h = MAX(1ul, texture.height >> mip);
                NSUInteger row = ((w * 4 + 255) / 256) * 256;
                id<MTLBuffer> output = [device newBufferWithLength:row * h options:MTLResourceStorageModeShared];
                id<MTLCommandBuffer> cb = [queue commandBuffer];
                id<MTLBlitCommandEncoder> blit = [cb blitCommandEncoder];
                [blit copyFromTexture:texture sourceSlice:0 sourceLevel:mip sourceOrigin:MTLOriginMake(0,0,0)
                    sourceSize:MTLSizeMake(w,h,1) toBuffer:output destinationOffset:0
                    destinationBytesPerRow:row destinationBytesPerImage:row*h];
                [blit endEncoding]; [cb commit]; [cb waitUntilCompleted];
                if (cb.status == MTLCommandBufferStatusError) {
                    fprintf(stderr, "%s\n", cb.error.localizedDescription.UTF8String); return 6;
                }
                NSMutableData *tight = [NSMutableData dataWithLength:w*h*4];
                for (NSUInteger y = 0; y < h; ++y) memcpy((char *)tight.mutableBytes + y*w*4, (char *)output.contents + y*row, w*4);
                NSString *name = [NSString stringWithFormat:@"decoded-%@-mip%lu.f32", [item[@"ref"] substringFromIndex:1], (unsigned long)mip];
                if (![tight writeToFile:[root stringByAppendingPathComponent:name] atomically:YES]) return 7;
                const float *f = (const float *)tight.bytes;
                float low = FLT_MAX, high = -FLT_MAX; NSUInteger finite = 0, nonzero = 0;
                for (NSUInteger n = 0; n < w*h; ++n) if (std::isfinite(f[n])) {
                    low = fminf(low,f[n]); high = fmaxf(high,f[n]); finite++; if (f[n] != 0) nonzero++;
                }
                NSMutableDictionary *level = [@{@"mip":@(mip),@"width":@(w),@"height":@(h),@"finite":@(finite),@"nonzero":@(nonzero),@"file":name} mutableCopy];
                if (finite) { level[@"minimum"] = @(low); level[@"maximum"] = @(high); }
                if (mip == 6) {
                    NSMutableArray *values = [NSMutableArray new];
                    for (NSUInteger n=0; n<w*h; ++n) [values addObject:std::isfinite(f[n]) ? @(f[n]) : (id)[NSNull null]];
                    level[@"values"] = values;
                }
                [levels addObject:level];
            }
            [results addObject:@{@"texture":item[@"ref"],@"levels":levels}];
        }
        NSData *json = [NSJSONSerialization dataWithJSONObject:results options:NSJSONWritingPrettyPrinted error:&error];
        if (!json || ![json writeToFile:[root stringByAppendingPathComponent:@"decoded-hiz.json"] atomically:YES]) return 8;
        printf("Reconstructed %lu captured textures and exported raw float mip levels. Fidelity still requires validation.\n", (unsigned long)textures.count);
    }
    return 0;
}
