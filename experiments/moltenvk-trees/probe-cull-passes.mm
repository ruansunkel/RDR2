// Compare the original, legacy bypass and pass-preserving bypass on captured
// small buffers with synthetic depth. This does not reproduce water rendering.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <vector>
#include <algorithm>
#define rdr2BypassCapturedTreeHiZ legacyTree
#include "tree-cull-hiz-workaround.h"
#undef rdr2BypassCapturedTreeHiZ
#define rdr2BypassCapturedFoliageHiZ legacyFoliage
#include "foliage-cull-hiz-workaround.h"
#undef rdr2BypassCapturedFoliageHiZ
#define rdr2BypassCapturedRockHiZ legacyRock
#include "rock-cull-hiz-workaround.h"
#undef rdr2BypassCapturedRockHiZ
#include "tree-cull-pass-safe-hiz-workaround.h"
#include "foliage-cull-pass-safe-hiz-workaround.h"
#include "rock-cull-pass-safe-hiz-workaround.h"

using Helper = bool (*)(std::string&, std::string*);

static void require(bool ok, const char *message) {
    if (!ok) { fprintf(stderr, "%s\n", message); exit(1); }
}

static NSData *input(NSString *root, NSString *kind, NSString *name) {
    NSString *file = [name isEqualToString:@"metal"] ?
        [NSString stringWithFormat:@"%@-cull.metal", kind] :
        [NSString stringWithFormat:@"%@-cull-%@", kind, name];
    NSString *path = [[root stringByAppendingPathComponent:kind] stringByAppendingPathComponent:file];
    NSData *data = [NSData dataWithContentsOfFile:path];
    require(data != nil, path.UTF8String);
    return data;
}

// Packed MSL _10, including four 112-byte shadow records. Assert these offsets
// against the captured values before changing them, rather than host SIMD layout.
static constexpr size_t hiZOffset = 376, flagsOffset = 892;

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 3) return 2;
        NSString *root = [NSString stringWithUTF8String:argv[1]];
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        require(device != nil, "No Metal device");
        id<MTLCommandQueue> queue = [device newCommandQueue];
        NSMutableArray *results = [NSMutableArray new];
        unsigned legacyDuplicates = 0, cases = 0;
        NSArray *kinds = @[@"tree", @"foliage", @"rock"];
        Helper legacy[] = {legacyTree, legacyFoliage, legacyRock};
        Helper fixed[] = {rdr2BypassCapturedTreeHiZ, rdr2BypassCapturedFoliageHiZ, rdr2BypassCapturedRockHiZ};
        for (unsigned k = 0; k < 3; ++k) {
            NSString *kind = kinds[k];
            NSData *sourceData = input(root, kind, @"metal");
            std::string original((const char *)sourceData.bytes, sourceData.length);
            std::string revised = original;
            require(fixed[k](revised, nullptr), "Captured shader did not match");
            std::string different = original + "\n// changed\n", before = different;
            require(!fixed[k](different, nullptr) && different == before, "Changed-source guard failed");
            different = "kernel void unrelated() {}"; before = different;
            require(!fixed[k](different, nullptr) && different == before, "Unrelated-source guard failed");
            std::string env = "RDR2_MVK_" + std::string(k == 0 ? "TREE" : k == 1 ? "FOLIAGE" : "ROCK") + "_HIZ_BYPASS";
            setenv(env.c_str(), "0", 1); different = original;
            require(!fixed[k](different, nullptr) && different == original, "Disabled-switch guard failed");
            unsetenv(env.c_str());
            different = "// alternate preamble\n" + original;
            require(fixed[k](different, nullptr), "Preamble guard rejected the same body");
            std::vector<uint32_t> sizes = k == 0 ? std::vector<uint32_t>{0,40,40,4,4,40,320,0,132,640} :
                k == 1 ? std::vector<uint32_t>{0,192,552,552,552,552,100,0,132,2208,3000} :
                         std::vector<uint32_t>{0,404,404,404,404,120,0,132,6464};
            NSArray *names = k == 0 ? @[@"camera",@"globals",@"aux",@"object",@"transforms",@"args"] :
                k == 1 ? @[@"camera",@"wind",@"aux",@"globals",@"clump",@"lod",@"object",@"transforms",@"extra",@"args"] :
                         @[@"camera",@"globals",@"object",@"transforms",@"args"];
            for (bool fast : {false, true}) {
                // Indexed by mode, HiZ gate, inversion flag and synthetic depth.
                NSMutableDictionary *outputs = [NSMutableDictionary new];
                for (unsigned mode = 0; mode < 3; ++mode) {
                    std::string source = original;
                    if (mode) require((mode == 1 ? legacy[k] : fixed[k])(source, nullptr), "Helper failed");
                    MTLCompileOptions *options = [MTLCompileOptions new];
                    options.fastMathEnabled = fast;
                    NSError *error = nil;
                    id<MTLLibrary> library = [device newLibraryWithSource:[NSString stringWithUTF8String:source.c_str()] options:options error:&error];
                    require(library != nil, error.localizedDescription.UTF8String);
                    id<MTLFunction> function = [library newFunctionWithName:@"VkMain"];
                    id<MTLComputePipelineState> pipeline = [device newComputePipelineStateWithFunction:function error:&error];
                    require(pipeline != nil, error.localizedDescription.UTF8String);
                    for (unsigned hiz = 0; hiz < 2; ++hiz) for (unsigned inverse = 0; inverse < 2; ++inverse)
                    for (unsigned depth : {0u, 300u, 10000u}) {
                        NSMutableDictionary *inputs = [NSMutableDictionary new];
                        for (NSString *name in names) {
                            NSData *data = input(root, kind, [name stringByAppendingString:@".bin"]);
                            inputs[name] = [device newBufferWithBytes:data.bytes length:data.length options:MTLResourceStorageModeShared];
                        }
                        id<MTLBuffer> globals = inputs[@"globals"], args = inputs[@"args"];
                        require(globals.length == 928, "Unexpected globals layout");
                        uint32_t *g = (uint32_t *)globals.contents;
                        require(g[hiZOffset/4] == 1 && g[flagsOffset/4] == 0xfe, "Captured global offsets differ");
                        g[hiZOffset/4] = hiz;
                        g[flagsOffset/4] = (g[flagsOffset/4] & ~1u) | inverse;
                        for (NSUInteger n = 0; n < args.length/20; ++n) ((uint32_t *)args.contents)[n*5+1] = 0;
                        id<MTLBuffer> sizeBuffer = [device newBufferWithBytes:sizes.data() length:sizes.size()*4 options:MTLResourceStorageModeShared];
                        NSMutableArray *lists = [NSMutableArray new];
                        for (unsigned n = 0; n < (k == 0 ? 5u : 4u); ++n) {
                            NSUInteger length = k == 0 ? ((n == 2 || n == 3) ? 4 : 40) : k == 1 ? 552 : 404;
                            id<MTLBuffer> list = [device newBufferWithLength:length options:MTLResourceStorageModeShared];
                            memset(list.contents, 0, list.length); [lists addObject:list];
                        }
                        MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR32Float width:128 height:72 mipmapped:YES];
                        td.mipmapLevelCount = 7; td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead;
                        id<MTLTexture> texture = [device newTextureWithDescriptor:td];
                        for (NSUInteger mip = 0; mip < 7; ++mip) {
                            NSUInteger w = MAX(1ul, 128ul >> mip), h = MAX(1ul, 72ul >> mip);
                            std::vector<float> pixels(w*h, float(depth));
                            [texture replaceRegion:MTLRegionMake2D(0,0,w,h) mipmapLevel:mip withBytes:pixels.data() bytesPerRow:w*4];
                        }
                        id<MTLArgumentEncoder> e0 = [function newArgumentEncoderWithBufferIndex:0], e1 = [function newArgumentEncoderWithBufferIndex:1];
                        id<MTLBuffer> set0 = [device newBufferWithLength:e0.encodedLength options:MTLResourceStorageModeShared];
                        id<MTLBuffer> set1 = [device newBufferWithLength:e1.encodedLength options:MTLResourceStorageModeShared];
                        [e0 setArgumentBuffer:set0 offset:0]; [e1 setArgumentBuffer:set1 offset:0];
                        [e0 setBuffer:sizeBuffer offset:0 atIndex:0]; [e1 setBuffer:sizeBuffer offset:0 atIndex:0];
                        NSArray *ds0 = k == 0 ? @[@"camera",@"globals",@"aux"] : k == 1 ? @[@"camera",@"wind",@"aux",@"globals",@"clump"] : @[@"camera",@"globals"];
                        for (NSUInteger n = 0; n < ds0.count; ++n) [e0 setBuffer:inputs[ds0[n]] offset:0 atIndex:n+1];
                        unsigned listBase = k == 1 ? 2 : 1, argIndex = k == 2 ? 5 : 6;
                        if (k == 1) [e1 setBuffer:inputs[@"lod"] offset:0 atIndex:1];
                        for (NSUInteger n = 0; n < lists.count; ++n) [e1 setBuffer:lists[n] offset:0 atIndex:n+listBase];
                        [e1 setBuffer:args offset:0 atIndex:argIndex]; [e1 setTexture:texture atIndex:argIndex+1];
                        [e1 setBuffer:inputs[@"object"] offset:0 atIndex:argIndex+2];
                        [e1 setBuffer:inputs[@"transforms"] offset:0 atIndex:argIndex+3];
                        if (k == 1) [e1 setBuffer:inputs[@"extra"] offset:0 atIndex:10];
                        id<MTLCommandBuffer> cb = [queue commandBuffer];
                        id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
                        [enc setComputePipelineState:pipeline]; [enc setBuffer:set0 offset:0 atIndex:0];
                        [enc setBuffer:set1 offset:0 atIndex:1]; [enc setBuffer:sizeBuffer offset:0 atIndex:29];
                        for (id<MTLBuffer> b in inputs.allValues) [enc useResource:b usage:MTLResourceUsageRead|MTLResourceUsageWrite];
                        for (id<MTLBuffer> b in lists) [enc useResource:b usage:MTLResourceUsageRead|MTLResourceUsageWrite];
                        [enc useResource:sizeBuffer usage:MTLResourceUsageRead]; [enc useResource:texture usage:MTLResourceUsageRead];
                        [enc dispatchThreadgroups:MTLSizeMake(k == 0 ? 1 : k == 1 ? 3 : 2,1,1) threadsPerThreadgroup:MTLSizeMake(64,1,1)];
                        [enc endEncoding]; [cb commit]; [cb waitUntilCompleted];
                        require(cb.status == MTLCommandBufferStatusCompleted, cb.error.localizedDescription.UTF8String);
                        NSMutableArray *counts = [NSMutableArray new], *selected = [NSMutableArray new];
                        for (NSUInteger n = 0; n < args.length/20; ++n) [counts addObject:@(((uint32_t *)args.contents)[n*5+1])];
                        unsigned count = ((uint32_t *)args.contents)[(k == 0 ? 10 : 0)*5+1];
                        require(count <= (k == 0 ? 10u : k == 1 ? 138u : 101u), "Output overflow");
                        id<MTLBuffer> list = lists[k == 0 ? 1 : 0];
                        for (unsigned n = 0; n < count; ++n) [selected addObject:@(((uint32_t *)list.contents)[n] & 65535u)];
                        [selected sortUsingSelector:@selector(compare:)];
                        NSString *key = [NSString stringWithFormat:@"%u/%u/%u/%u",mode,hiz,inverse,depth];
                        NSDictionary *output = @{@"counts":counts,@"ids":selected}; outputs[key] = output;
                        [results addObject:@{@"shader":kind,@"mode":@(mode),@"fast":@(fast),@"hiz":@(hiz),@"inverse":@(inverse),@"depth":@(depth),@"output":output}];
                        ++cases;
                    }
                }
                for (unsigned hiz = 0; hiz < 2; ++hiz) for (unsigned inverse = 0; inverse < 2; ++inverse)
                for (unsigned depth : {0u, 300u, 10000u}) {
                    NSString *tail = [NSString stringWithFormat:@"/%u/%u/%u",hiz,inverse,depth];
                    NSDictionary *candidate = outputs[[@"2" stringByAppendingString:tail]];
                    // Candidate agrees with original all-visible depth, including
                    // inversion; disabled HiZ must retain original behavior.
                    NSString *ref = [NSString stringWithFormat:@"0/%u/%u/0",hiz,inverse];
                    require([candidate isEqual:outputs[ref]], "Candidate violates pass/gate semantics");
                    if (!hiz || !inverse)
                        require([candidate isEqual:outputs[[@"1" stringByAppendingString:tail]]], "Normal-view fix changed");
                    if (hiz && inverse) {
                        require([candidate[@"ids"] count] == 0, "Inverted pass includes visible instances");
                        if ([outputs[[@"1" stringByAppendingString:tail]][@"ids"] count]) ++legacyDuplicates;
                    }
                }
                NSArray *normal = outputs[@"2/1/0/10000"][@"ids"];
                require([normal containsObject:@(k == 0 ? 3 : k == 1 ? 17 : 73)], "Previously missing instance lost");
                printf("%s %s: pass controls and original disappearing-instance regression passed\n",kind.UTF8String,fast ? "fast" : "precise");
            }
        }
        require(legacyDuplicates == 18, "Did not reproduce legacy inverse-pass defect for every shader/depth/math case");
        NSDictionary *report = @{@"gpu":device.name,@"cases":@(cases),@"legacy_inverse_failures":@(legacyDuplicates),
            @"pass_controls_passed":@YES,@"guard_controls_passed":@YES,@"original_instances_retained":@YES,
            @"synthetic_depth":@YES,@"water_rendering_verified":@NO,@"results":results};
        NSData *json = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:nil];
        require([json writeToFile:[NSString stringWithUTF8String:argv[2]] options:NSDataWritingWithoutOverwriting error:nil], "Could not write new report");
        printf("%u GPU cases passed; %u legacy inverse-pass failures reproduced.\n",cases,legacyDuplicates);
    }
    return 0;
}
