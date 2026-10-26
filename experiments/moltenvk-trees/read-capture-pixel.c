// Read-only pixel probe for exported GPU attachments; never edits an image.
#include <CoreFoundation/CoreFoundation.h>
#include <CoreGraphics/CoreGraphics.h>
#include <ImageIO/ImageIO.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    CFURLRef url = CFURLCreateFromFileSystemRepresentation(NULL, (const UInt8 *)argv[1], strlen(argv[1]), false);
    CGImageSourceRef source = CGImageSourceCreateWithURL(url, NULL);
    if (!source) return 3;
    CGImageRef image = CGImageSourceCreateImageAtIndex(source, 0, NULL);
    if (!image) return 4;
    size_t width = CGImageGetWidth(image), height = CGImageGetHeight(image);
    long x = strtol(argv[2], NULL, 10), y = strtol(argv[3], NULL, 10);
    if (x < 0 || y < 0 || x >= (long)width || y >= (long)height) return 5;
    CGColorSpaceRef color = CGColorSpaceCreateDeviceRGB();
    CGContextRef context = CGBitmapContextCreate(NULL, width, height, 8, width * 4, color,
        kCGImageAlphaPremultipliedLast | kCGBitmapByteOrder32Big);
    if (!context) return 6;
    CGContextDrawImage(context, CGRectMake(0, 0, width, height), image);
    const unsigned char *data = CGBitmapContextGetData(context);
    const unsigned char *p = data + ((size_t)y * width + (size_t)x) * 4;
    printf("{\"x\":%ld,\"y\":%ld,\"rgba\":[%u,%u,%u,%u],\"width\":%zu,\"height\":%zu}\n",
        x, y, p[0], p[1], p[2], p[3], width, height);
    CGContextRelease(context); CGColorSpaceRelease(color);
    CGImageRelease(image); CFRelease(source); CFRelease(url);
    return 0;
}
