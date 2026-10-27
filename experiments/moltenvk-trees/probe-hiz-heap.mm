// Synthetic texture-integrity comparison using the captured HiZ placements.
// This does not reconstruct captured depth or reproduce the complete game.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <cmath>

static void fail(NSString *message) {
    fprintf(stderr, "%s\n", message.UTF8String);
    exit(2);
}

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 3) return 2;
        NSData *input = [NSData dataWithContentsOfFile:[NSString stringWithUTF8String:argv[1]]];
        NSError *error = nil;
        NSArray *placements = input ? [NSJSONSerialization JSONObjectWithData:input options:0 error:&error] : nil;
        if (![placements isKindOfClass:NSArray.class] || !placements.count || error) fail(@"Invalid placements");
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) fail(@"No Metal device");
        NSString *source = @"#include <metal_stdlib>\nusing namespace metal;\n"
            "vertex float4 vs(uint n [[vertex_id]]) { return float4(float2((n<<1)&2,n&2)*2.0-1.0,0,1); }\n"
            "fragment float fs(float4 p [[position]], constant uint& token [[buffer(0)]]) { return float(token+uint(p.x)+uint(p.y)*128u); }\n"
            "struct Resources { texture2d<float> depth [[id(0)]]; };\n"
            "kernel void cs(constant Resources& r [[buffer(0)]], device float* dst [[buffer(1)]], constant uint& mip [[buffer(2)]], uint2 p [[thread_position_in_grid]]) {\n"
            " if(p.x<r.depth.get_width(mip) && p.y<r.depth.get_height(mip)) dst[p.y*r.depth.get_width(mip)+p.x]=r.depth.read(p,mip).x; }\n";
        id<MTLLibrary> library = [device newLibraryWithSource:source options:nil error:&error];
        if (!library) fail(error.localizedDescription);
        MTLRenderPipelineDescriptor *rd = [MTLRenderPipelineDescriptor new];
        rd.vertexFunction = [library newFunctionWithName:@"vs"];
        rd.fragmentFunction = [library newFunctionWithName:@"fs"];
        rd.colorAttachments[0].pixelFormat = MTLPixelFormatR32Float;
        id<MTLRenderPipelineState> render = [device newRenderPipelineStateWithDescriptor:rd error:&error];
        id<MTLFunction> function = [library newFunctionWithName:@"cs"];
        id<MTLComputePipelineState> compute = [device newComputePipelineStateWithFunction:function error:&error];
        if (!render || !compute) fail(error.localizedDescription);
        id<MTLCommandQueue> queue = [device newCommandQueue];
        NSMutableArray *results = [NSMutableArray new];
        NSUInteger totalMismatches = 0;
        for (NSString *mode in @[@"standalone", @"placement", @"placement-with-parent-buffer"]) {
            @autoreleasepool {
                MTLHeapDescriptor *hd = [MTLHeapDescriptor new];
                hd.type = MTLHeapTypePlacement;
                hd.storageMode = MTLStorageModeShared;
                hd.hazardTrackingMode = MTLHazardTrackingModeTracked;
                hd.size = 32 * 1024 * 1024;
                id<MTLHeap> heap = [mode isEqualToString:@"standalone"] ? nil : [device newHeapWithDescriptor:hd];
                if (![mode isEqualToString:@"standalone"] && !heap) fail(@"Heap creation failed");
                __attribute__((objc_precise_lifetime)) id<MTLBuffer> parent = nil;
                if ([mode isEqualToString:@"placement-with-parent-buffer"]) {
                    parent = [heap newBufferWithLength:hd.size options:MTLResourceStorageModeShared offset:0];
                    if (!parent) fail(@"Parent buffer creation failed");
                    [parent makeAliasable];
                }
                NSMutableArray *textures = [NSMutableArray new], *sets = [NSMutableArray new];
                NSMutableArray *ranges = [NSMutableArray new];
                for (NSDictionary *placement in placements) {
                    NSUInteger w = [placement[@"width"] unsignedIntegerValue], h = [placement[@"height"] unsignedIntegerValue];
                    NSUInteger levels = [placement[@"levels"] unsignedIntegerValue], offset = [placement[@"offset"] unsignedIntegerValue];
                    if (w != 128 || h != 72 || levels != 7) fail(@"Unexpected captured HiZ dimensions");
                    MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR32Float width:w height:h mipmapped:YES];
                    td.mipmapLevelCount = levels;
                    td.storageMode = MTLStorageModeShared;
                    td.usage = MTLTextureUsageShaderRead | MTLTextureUsageRenderTarget;
                    td.allowGPUOptimizedContents = YES;
                    MTLSizeAndAlign size = [device heapTextureSizeAndAlignWithDescriptor:td];
                    if (offset % size.align || offset > hd.size || size.size > hd.size - offset) fail(@"Invalid heap placement");
                    NSRange range = NSMakeRange(offset, size.size);
                    for (NSValue *prior in ranges) if (NSIntersectionRange(range, prior.rangeValue).length) fail(@"Overlapping captured texture placements");
                    [ranges addObject:[NSValue valueWithRange:range]];
                    id<MTLTexture> texture = heap ? [heap newTextureWithDescriptor:td offset:offset] : [device newTextureWithDescriptor:td];
                    if (!texture) fail(@"Texture creation failed");
                    [textures addObject:texture];
                    id<MTLArgumentEncoder> encoder = [function newArgumentEncoderWithBufferIndex:0];
                    id<MTLBuffer> set = [device newBufferWithLength:encoder.encodedLength options:MTLResourceStorageModeShared];
                    [encoder setArgumentBuffer:set offset:0];
                    [encoder setTexture:texture atIndex:0];
                    [sets addObject:set];
                }
                NSUInteger checked = 0, mismatches = 0;
                NSMutableArray *examples = [NSMutableArray new];
                for (uint32_t frame = 0; frame < 8; ++frame) {
                    id<MTLCommandBuffer> cb = [queue commandBuffer];
                    NSMutableArray *outputs = [NSMutableArray new];
                    // Write every texture before reading any: catch cross-texture corruption.
                    for (NSUInteger i = 0; i < textures.count; ++i) {
                        id<MTLTexture> texture = textures[i];
                        for (NSUInteger mip = 0; mip < texture.mipmapLevelCount; ++mip) {
                            MTLRenderPassDescriptor *pass = [MTLRenderPassDescriptor renderPassDescriptor];
                            pass.colorAttachments[0].texture = texture;
                            pass.colorAttachments[0].level = mip;
                            pass.colorAttachments[0].loadAction = MTLLoadActionDontCare;
                            pass.colorAttachments[0].storeAction = MTLStoreActionStore;
                            id<MTLRenderCommandEncoder> enc = [cb renderCommandEncoderWithDescriptor:pass];
                            uint32_t token = frame * 20000 + (uint32_t)i * 1000 + (uint32_t)mip * 100;
                            [enc setRenderPipelineState:render];
                            [enc setFragmentBytes:&token length:sizeof(token) atIndex:0];
                            [enc drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:3];
                            [enc endEncoding];
                        }
                    }
                    for (NSUInteger i = 0; i < textures.count; ++i) {
                        id<MTLTexture> texture = textures[i];
                        for (uint32_t mip = 0; mip < texture.mipmapLevelCount; ++mip) {
                            NSUInteger w = MAX(1ul, texture.width >> mip), h = MAX(1ul, texture.height >> mip);
                            id<MTLBuffer> output = [device newBufferWithLength:w*h*sizeof(float) options:MTLResourceStorageModeShared];
                            [outputs addObject:output];
                            id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
                            [enc setComputePipelineState:compute];
                            [enc setBuffer:sets[i] offset:0 atIndex:0];
                            [enc setBuffer:output offset:0 atIndex:1];
                            [enc setBytes:&mip length:sizeof(mip) atIndex:2];
                            [enc useResource:texture usage:MTLResourceUsageRead];
                            [enc dispatchThreads:MTLSizeMake(w,h,1) threadsPerThreadgroup:MTLSizeMake(8,8,1)];
                            [enc endEncoding];
                        }
                    }
                    [cb commit]; [cb waitUntilCompleted];
                    if (cb.status != MTLCommandBufferStatusCompleted) fail(cb.error.localizedDescription ?: @"GPU execution failed");
                    NSUInteger n = 0;
                    for (NSUInteger i = 0; i < textures.count; ++i) {
                        id<MTLTexture> texture = textures[i];
                        for (NSUInteger mip = 0; mip < texture.mipmapLevelCount; ++mip) {
                            NSUInteger w = MAX(1ul, texture.width >> mip), h = MAX(1ul, texture.height >> mip);
                            id<MTLBuffer> output = outputs[n++];
                            const float *values = (const float *)output.contents;
                            for (NSUInteger y = 0; y < h; ++y) for (NSUInteger x = 0; x < w; ++x) {
                                float expected = float(frame*20000+i*1000+mip*100+x+y*128);
                                float actual = values[y*w+x];
                                ++checked;
                                if (actual != expected) {
                                    ++mismatches;
                                    if (examples.count < 16) [examples addObject:@{@"frame":@(frame), @"texture":@(i), @"mip":@(mip), @"x":@(x), @"y":@(y), @"expected":@(expected), @"actual":std::isfinite(actual) ? @(actual) : (id)NSNull.null}];
                                }
                            }
                        }
                    }
                }
                totalMismatches += mismatches;
                [results addObject:@{@"mode":mode, @"frames":@8, @"textures":@(textures.count), @"checked_values":@(checked), @"mismatches":@(mismatches), @"examples":examples}];
                printf("%s: %lu values, %lu mismatches\n",mode.UTF8String,(unsigned long)checked,(unsigned long)mismatches);
                (void)parent; // Keep the overlapping parent buffer alive through GPU completion.
            }
        }
        NSDictionary *report = @{@"gpu":device.name, @"synthetic_depth_controls":@YES, @"game_hiz_data_reproduced":@NO, @"game_heap_fault_reproduced":@NO, @"results":results};
        NSData *json = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:&error];
        if (!json || ![json writeToFile:[NSString stringWithUTF8String:argv[2]] options:NSDataWritingWithoutOverwriting error:&error]) fail(error.localizedDescription ?: @"Cannot write report");
        return totalMismatches ? 3 : 0;
    }
}
