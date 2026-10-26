// Exercise the candidate's dedicated-buffer path and required image heaps on a
// real Metal device. This is a focused Vulkan smoke test, not a visual game test.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define FUNCTIONS(X) \
 X(vkCreateInstance) X(vkDestroyInstance) X(vkEnumeratePhysicalDevices) \
 X(vkGetPhysicalDeviceProperties) X(vkGetPhysicalDeviceQueueFamilyProperties) \
 X(vkGetPhysicalDeviceMemoryProperties) X(vkCreateDevice) X(vkDestroyDevice) \
 X(vkGetDeviceQueue) X(vkCreateBuffer) X(vkGetBufferMemoryRequirements) \
 X(vkAllocateMemory) X(vkBindBufferMemory) X(vkMapMemory) X(vkUnmapMemory) \
 X(vkCreateCommandPool) X(vkAllocateCommandBuffers) X(vkBeginCommandBuffer) \
 X(vkCmdCopyBuffer) X(vkCmdPipelineBarrier) X(vkEndCommandBuffer) \
 X(vkCreateFence) X(vkQueueSubmit) X(vkWaitForFences) X(vkDeviceWaitIdle) \
 X(vkCreateImage) X(vkGetImageMemoryRequirements) X(vkBindImageMemory) \
 X(vkCreateImageView) X(vkDestroyImageView) X(vkDestroyImage) \
 X(vkDestroyBuffer) X(vkFreeMemory) X(vkDestroyFence) X(vkDestroyCommandPool)
#define DECLARE(name) static PFN_##name name;
FUNCTIONS(DECLARE)
#define CHECK(call) do { VkResult result = (call); if (result != VK_SUCCESS) { \
    fprintf(stderr, "%s failed: %d\n", #call, result); exit(1); } } while (0)

static uint32_t memory_type(VkPhysicalDeviceMemoryProperties* props, uint32_t bits,
                            VkMemoryPropertyFlags flags) {
    for (uint32_t i = 0; i < props->memoryTypeCount; ++i) {
        if ((bits & (1u << i)) && (props->memoryTypes[i].propertyFlags & flags) == flags) return i;
    }
    fprintf(stderr, "Required memory type unavailable\n"); exit(1);
}

int main(int argc, char** argv) {
    if (argc != 2) { fprintf(stderr, "Usage: probe-gpu ABSOLUTE_MOLTENVK_DYLIB\n"); return 2; }
    void* library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 1; }
#define LOAD(name) name = (PFN_##name)dlsym(library, #name); \
    if (!name) { fprintf(stderr, "Missing %s\n", #name); return 1; }
    FUNCTIONS(LOAD)
    VkApplicationInfo application = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "RDR2 allocation smoke probe", .apiVersion = VK_API_VERSION_1_1};
    // Call the ICD directly: portability enumeration belongs to a Vulkan loader
    // and is not an instance extension of MoltenVK itself.
    VkInstanceCreateInfo instance_info = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &application};
    VkInstance instance;
    CHECK(vkCreateInstance(&instance_info, NULL, &instance));
    uint32_t count = 0;
    CHECK(vkEnumeratePhysicalDevices(instance, &count, NULL));
    if (!count) { fprintf(stderr, "No Vulkan GPU available\n"); return 1; }
    VkPhysicalDevice* devices = calloc(count, sizeof(*devices));
    CHECK(vkEnumeratePhysicalDevices(instance, &count, devices));
    VkPhysicalDevice gpu = devices[0]; free(devices);
    VkPhysicalDeviceProperties properties;
    vkGetPhysicalDeviceProperties(gpu, &properties);
    printf("GPU: %s; native probe PID: %ld\n", properties.deviceName, (long)getpid());
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, NULL);
    VkQueueFamilyProperties* families = calloc(count, sizeof(*families));
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, families);
    uint32_t family = UINT32_MAX;
    for (uint32_t i = 0; i < count; ++i) if (families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { family = i; break; }
    free(families);
    if (family == UINT32_MAX) { fprintf(stderr, "No graphics queue\n"); return 1; }
    float priority = 1.0f;
    VkDeviceQueueCreateInfo queue_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = family, .queueCount = 1, .pQueuePriorities = &priority};
    const char* device_extensions[] = {"VK_KHR_portability_subset"};
    VkDeviceCreateInfo device_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1, .pQueueCreateInfos = &queue_info,
        .enabledExtensionCount = 1, .ppEnabledExtensionNames = device_extensions};
    VkDevice device;
    CHECK(vkCreateDevice(gpu, &device_info, NULL, &device));
    VkQueue queue; vkGetDeviceQueue(device, family, 0, &queue);
    VkPhysicalDeviceMemoryProperties memory;
    vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
    VkBuffer buffers[2]; VkDeviceMemory allocations[2]; void* mappings[2];
    for (unsigned i = 0; i < 2; ++i) {
        VkBufferCreateInfo info = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            .size = 4096, .usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
            .sharingMode = VK_SHARING_MODE_EXCLUSIVE};
        CHECK(vkCreateBuffer(device, &info, NULL, &buffers[i]));
        VkMemoryRequirements requirements;
        vkGetBufferMemoryRequirements(device, buffers[i], &requirements);
        VkMemoryDedicatedAllocateInfo dedicated = {.sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
            .buffer = buffers[i]};
        VkMemoryAllocateInfo allocation = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            .pNext = &dedicated, .allocationSize = requirements.size,
            .memoryTypeIndex = memory_type(&memory, requirements.memoryTypeBits,
                VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)};
        CHECK(vkAllocateMemory(device, &allocation, NULL, &allocations[i]));
        CHECK(vkBindBufferMemory(device, buffers[i], allocations[i], 0));
        CHECK(vkMapMemory(device, allocations[i], 0, 4096, 0, &mappings[i]));
        memset(mappings[i], i ? 0 : 0xa7, 4096);
    }
    VkCommandPoolCreateInfo pool_info = {.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = family};
    VkCommandPool pool; CHECK(vkCreateCommandPool(device, &pool_info, NULL, &pool));
    VkCommandBufferAllocateInfo allocate_commands = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = pool, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1};
    VkCommandBuffer command; CHECK(vkAllocateCommandBuffers(device, &allocate_commands, &command));
    VkCommandBufferBeginInfo begin = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};
    CHECK(vkBeginCommandBuffer(command, &begin));
    VkBufferCopy copy = {.size = 4096}; vkCmdCopyBuffer(command, buffers[0], buffers[1], 1, &copy);
    VkMemoryBarrier barrier = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
        .srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT, .dstAccessMask = VK_ACCESS_HOST_READ_BIT};
    vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
        0, 1, &barrier, 0, NULL, 0, NULL);
    CHECK(vkEndCommandBuffer(command));
    VkFenceCreateInfo fence_info = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VkFence fence; CHECK(vkCreateFence(device, &fence_info, NULL, &fence));
    VkSubmitInfo submit = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1, .pCommandBuffers = &command};
    CHECK(vkQueueSubmit(queue, 1, &submit, fence));
    CHECK(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ull));
    for (unsigned i = 0; i < 4096; ++i) if (((uint8_t*)mappings[1])[i] != 0xa7) {
        fprintf(stderr, "GPU copy data mismatch\n"); return 1;
    }
    puts("Dedicated-buffer GPU copy: passed");
    VkImageCreateInfo image_info = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .flags = VK_IMAGE_CREATE_2D_ARRAY_COMPATIBLE_BIT, .imageType = VK_IMAGE_TYPE_3D,
        .format = VK_FORMAT_R8G8B8A8_UNORM, .extent = {4, 4, 4}, .mipLevels = 1, .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
        .usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE, .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VkImage image; CHECK(vkCreateImage(device, &image_info, NULL, &image));
    VkMemoryRequirements image_requirements; vkGetImageMemoryRequirements(device, image, &image_requirements);
    VkMemoryDedicatedAllocateInfo image_dedicated = {.sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO, .image = image};
    VkMemoryAllocateInfo image_allocation = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .pNext = &image_dedicated,
        .allocationSize = image_requirements.size,
        .memoryTypeIndex = memory_type(&memory, image_requirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)};
    VkDeviceMemory image_memory; CHECK(vkAllocateMemory(device, &image_allocation, NULL, &image_memory));
    CHECK(vkBindImageMemory(device, image, image_memory, 0));
    VkImageViewCreateInfo view_info = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = image, .viewType = VK_IMAGE_VIEW_TYPE_2D_ARRAY, .format = image_info.format,
        .subresourceRange = {.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT, .levelCount = 1, .layerCount = 4}};
    VkImageView view; CHECK(vkCreateImageView(device, &view_info, NULL, &view));
    puts("3D image with heap-backed 2D array view: passed");
    CHECK(vkDeviceWaitIdle(device));
    vkDestroyImageView(device, view, NULL); vkDestroyImage(device, image, NULL); vkFreeMemory(device, image_memory, NULL);
    for (unsigned i = 0; i < 2; ++i) {
        vkUnmapMemory(device, allocations[i]); vkDestroyBuffer(device, buffers[i], NULL); vkFreeMemory(device, allocations[i], NULL);
    }
    vkDestroyFence(device, fence, NULL); vkDestroyCommandPool(device, pool, NULL);
    vkDestroyDevice(device, NULL); vkDestroyInstance(instance, NULL); dlclose(library);
    return 0;
}
