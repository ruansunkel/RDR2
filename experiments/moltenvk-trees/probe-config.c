// Build-only diagnostic: query a chosen MoltenVK dylib without creating a device
// or launching Wine. Uses the pinned upstream API headers, not guessed offsets.
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "mvk_private_api.h"
#include "mvk_deprecated_api.h"

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) { fprintf(stderr, "Usage: probe-config ABSOLUTE_DYLIB [HOLD_SECONDS]\n"); return 2; }
    long hold = 0;
    if (argc == 3) {
        char *end;
        hold = strtol(argv[2], &end, 10);
        if (*end || hold < 0 || hold > 60) { return 2; }
    }
    void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 1; }
    PFN_vkGetMoltenVKConfigurationMVK query = (PFN_vkGetMoltenVKConfigurationMVK)dlsym(library, "vkGetMoltenVKConfigurationMVK");
    PFN_vkGetVersionStringsMVK version = (PFN_vkGetVersionStringsMVK)dlsym(library, "vkGetVersionStringsMVK");
    if (!query || !version) { fprintf(stderr, "Required MoltenVK diagnostic exports missing.\n"); return 1; }
    size_t size = 0;
    query(VK_NULL_HANDLE, NULL, &size);
    if (size != sizeof(MVKConfiguration)) {
        fprintf(stderr, "Configuration ABI differs: library %zu, header %zu.\n", size, sizeof(MVKConfiguration));
        return 1;
    }
    MVKConfiguration config = {0};
    if (query(VK_NULL_HANDLE, &config, &size) != VK_SUCCESS) { return 1; }
    char mvk[256] = {0}, vk[256] = {0};
    version(mvk, sizeof(mvk), vk, sizeof(vk));
    printf("MoltenVK: %s\nVulkan: %s\nConfiguration ABI bytes: %zu\n", mvk, vk, size);
    printf("useMTLHeap: %d\nuseMetalArgumentBuffers: %u\nuseMetalPrivateAPI: %u\nliveCheckAllResources: %u\n",
           config.useMTLHeap, config.useMetalArgumentBuffers, config.useMetalPrivateAPI, config.liveCheckAllResources);
    fflush(stdout);
    if (hold) { sleep((unsigned int)hold); }
    return 0;
}
