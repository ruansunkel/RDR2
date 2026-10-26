// Real Vulkan regression for MoltenVK PR #2794's nonzero query result offset.
// No game files, settings or shaders are read. Run in a fresh process per dylib.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <dlfcn.h>
#include <stdint.h>
#include <inttypes.h>
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
 X(vkCreateQueryPool) X(vkDestroyQueryPool) X(vkCmdResetQueryPool) \
 X(vkCmdWriteTimestamp) X(vkCmdCopyQueryPoolResults) X(vkGetQueryPoolResults) \
 X(vkCmdPipelineBarrier) X(vkEndCommandBuffer) X(vkQueueSubmit) X(vkQueueWaitIdle) \
 X(vkDestroyBuffer) X(vkFreeMemory) X(vkDestroyCommandPool)
#define DECLARE(name) static PFN_##name name;
FUNCTIONS(DECLARE)
#define CHECK(call) do { VkResult result = (call); if (result != VK_SUCCESS) { \
 fprintf(stderr, "%s failed: %d\n", #call, result); exit(1); } } while (0)

static uint32_t memory_type(VkPhysicalDeviceMemoryProperties* props, uint32_t bits) {
 const VkMemoryPropertyFlags flags = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
 for (uint32_t i = 0; i < props->memoryTypeCount; ++i)
  if ((bits & (1u << i)) && (props->memoryTypes[i].propertyFlags & flags) == flags) return i;
 fprintf(stderr, "Host-visible coherent memory unavailable\n"); exit(1);
}
static void submit_wait(VkQueue queue, VkCommandBuffer command) {
 CHECK(vkEndCommandBuffer(command));
 VkSubmitInfo submit = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1, .pCommandBuffers = &command};
 CHECK(vkQueueSubmit(queue, 1, &submit, VK_NULL_HANDLE));
 CHECK(vkQueueWaitIdle(queue));
}
int main(int argc, char** argv) {
 if (argc != 2) { fprintf(stderr, "Usage: probe-queries ABSOLUTE_MOLTENVK_DYLIB\n"); return 2; }
 void* library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
 if (!library) { fprintf(stderr, "%s\n", dlerror()); return 1; }
#define LOAD(name) name = (PFN_##name)dlsym(library, #name); if (!name) { fprintf(stderr, "Missing %s\n", #name); return 1; }
 FUNCTIONS(LOAD)
 VkApplicationInfo application = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
  .pApplicationName = "RDR2 query range regression probe", .apiVersion = VK_API_VERSION_1_1};
 VkInstanceCreateInfo instance_info = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &application};
 VkInstance instance; CHECK(vkCreateInstance(&instance_info, NULL, &instance));
 uint32_t count = 0; CHECK(vkEnumeratePhysicalDevices(instance, &count, NULL));
 if (!count) { fprintf(stderr, "No Vulkan GPU\n"); return 1; }
 VkPhysicalDevice* devices = calloc(count, sizeof(*devices));
 CHECK(vkEnumeratePhysicalDevices(instance, &count, devices));
 VkPhysicalDevice gpu = devices[0]; free(devices);
 VkPhysicalDeviceProperties properties; vkGetPhysicalDeviceProperties(gpu, &properties);
 fprintf(stderr, "GPU: %s; native probe PID: %ld\n", properties.deviceName, (long)getpid());
 vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, NULL);
 VkQueueFamilyProperties* families = calloc(count, sizeof(*families));
 vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, families);
 uint32_t family = UINT32_MAX;
 for (uint32_t i = 0; i < count; ++i)
  if ((families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) && families[i].timestampValidBits) { family = i; break; }
 free(families);
 if (family == UINT32_MAX) { fprintf(stderr, "No graphics timestamp queue\n"); return 1; }
 float priority = 1.0f;
 VkDeviceQueueCreateInfo queue_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
  .queueFamilyIndex = family, .queueCount = 1, .pQueuePriorities = &priority};
 const char* extensions[] = {"VK_KHR_portability_subset"};
 VkDeviceCreateInfo device_info = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
  .queueCreateInfoCount = 1, .pQueueCreateInfos = &queue_info,
  .enabledExtensionCount = 1, .ppEnabledExtensionNames = extensions};
 VkDevice device; CHECK(vkCreateDevice(gpu, &device_info, NULL, &device));
 VkQueue queue; vkGetDeviceQueue(device, family, 0, &queue);
 VkPhysicalDeviceMemoryProperties memory; vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
 VkBufferCreateInfo buffer_info = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
  .size = 128, .usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE};
 VkBuffer buffer; CHECK(vkCreateBuffer(device, &buffer_info, NULL, &buffer));
 VkMemoryRequirements requirements; vkGetBufferMemoryRequirements(device, buffer, &requirements);
 VkMemoryAllocateInfo allocation = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
  .allocationSize = requirements.size, .memoryTypeIndex = memory_type(&memory, requirements.memoryTypeBits)};
 VkDeviceMemory allocated; CHECK(vkAllocateMemory(device, &allocation, NULL, &allocated));
 CHECK(vkBindBufferMemory(device, buffer, allocated, 0));
 void* mapping; CHECK(vkMapMemory(device, allocated, 0, 128, 0, &mapping));
 memset(mapping, 0xa5, 128);
 VkQueryPool pools[2];
 VkQueryPoolCreateInfo query_info = {.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO,
  .queryType = VK_QUERY_TYPE_TIMESTAMP, .queryCount = 8};
 for (unsigned i = 0; i < 2; ++i) CHECK(vkCreateQueryPool(device, &query_info, NULL, &pools[i]));
 VkCommandPoolCreateInfo pool_info = {.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .queueFamilyIndex = family};
 VkCommandPool pool; CHECK(vkCreateCommandPool(device, &pool_info, NULL, &pool));
 VkCommandBufferAllocateInfo commands_info = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
  .commandPool = pool, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 2};
 VkCommandBuffer commands[2]; CHECK(vkAllocateCommandBuffers(device, &commands_info, commands));
 VkCommandBufferBeginInfo begin = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
  .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};
 CHECK(vkBeginCommandBuffer(commands[0], &begin));
 for (unsigned i = 0; i < 2; ++i) vkCmdResetQueryPool(commands[0], pools[i], 0, 8);
 // Leave pool0 slot0 Initial. Only slot4 is made available. A second pool
 // tests slot0 independently so it cannot accidentally hide the regression.
 vkCmdWriteTimestamp(commands[0], VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, pools[0], 4);
 vkCmdWriteTimestamp(commands[0], VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, pools[1], 0);
 submit_wait(queue, commands[0]);
 uint64_t host_results[2] = {0, 0};
 CHECK(vkGetQueryPoolResults(device, pools[0], 4, 1, sizeof(host_results), host_results,
  sizeof(host_results), VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT | VK_QUERY_RESULT_WAIT_BIT));
 if (host_results[1] != 1) { fprintf(stderr, "Host slot4 query is not available\n"); return 1; }
 CHECK(vkBeginCommandBuffer(commands[1], &begin));
 VkQueryResultFlags flags = VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT | VK_QUERY_RESULT_WAIT_BIT;
 vkCmdCopyQueryPoolResults(commands[1], pools[0], 4, 1, buffer, 0, 16, flags);
 vkCmdCopyQueryPoolResults(commands[1], pools[0], 4, 1, buffer, 16, 8, flags & ~VK_QUERY_RESULT_64_BIT);
 vkCmdCopyQueryPoolResults(commands[1], pools[1], 0, 1, buffer, 32, 16, flags);
 VkMemoryBarrier barrier = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
  .srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT, .dstAccessMask = VK_ACCESS_HOST_READ_BIT};
 vkCmdPipelineBarrier(commands[1], VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
  0, 1, &barrier, 0, NULL, 0, NULL);
 submit_wait(queue, commands[1]);
 uint64_t* nonzero64 = (uint64_t*)mapping;
 uint32_t* nonzero32 = (uint32_t*)((uint8_t*)mapping + 16);
 uint64_t* zero64 = (uint64_t*)((uint8_t*)mapping + 32);
 int fixed = nonzero64[0] == host_results[0] && nonzero64[1] == 1 &&
  nonzero32[0] == (uint32_t)host_results[0] && nonzero32[1] == 1 && zero64[1] == 1;
 printf("QUERY_RESULT_JSON {\"pid\":%ld,\"host_available\":%" PRIu64 ",\"nonzero64_available\":%" PRIu64
  ",\"nonzero32_available\":%" PRIu32 ",\"zero64_available\":%" PRIu64 ",\"nonzero64_matches_host\":%s,\"nonzero32_matches_host\":%s,\"passed\":%s}\n",
  (long)getpid(), host_results[1], nonzero64[1], nonzero32[1], zero64[1],
  nonzero64[0] == host_results[0] ? "true" : "false", nonzero32[0] == (uint32_t)host_results[0] ? "true" : "false", fixed ? "true" : "false");
 for (unsigned i = 0; i < 2; ++i) vkDestroyQueryPool(device, pools[i], NULL);
 vkUnmapMemory(device, allocated); vkDestroyBuffer(device, buffer, NULL); vkFreeMemory(device, allocated, NULL);
 vkDestroyCommandPool(device, pool, NULL); vkDestroyDevice(device, NULL); vkDestroyInstance(instance, NULL); dlclose(library);
 return fixed ? 0 : 3;
}
