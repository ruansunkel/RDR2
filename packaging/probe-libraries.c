/* Build-only x86_64 dynamic-load probe. Never shipped as a host prerequisite. */
#include <dlfcn.h>
#include <stdio.h>

int main(int argc, char **argv) {
    for (int i = 1; i < argc; ++i) {
        void *library = dlopen(argv[i], RTLD_NOW | RTLD_LOCAL);
        if (!library) {
            fprintf(stderr, "Dynamic library check failed: %s\n", dlerror());
            return 1;
        }
        puts("Dynamic library loaded successfully.");
        dlclose(library);
    }
    return 0;
}
