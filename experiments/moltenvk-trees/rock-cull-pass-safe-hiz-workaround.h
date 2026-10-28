// Diagnostic workaround for the complete captured rigid-rock culling shader.
// The original numeric HiZ input is not reproduced by the synthetic controls.
#pragma once
#include <CommonCrypto/CommonDigest.h>
#include <cstdlib>
#include <cstring>
#include <string>

static bool rdr2BypassCapturedRockHiZ(std::string& source, std::string* fingerprint = nullptr) {
    const char* branch = "if (((*spvDescriptorSet0.m_12)._m0[0u]._m5 != 0u) && _542)";
    auto pos = source.find(branch);
    auto start = source.find("#include <metal_stdlib>");
    if (pos == std::string::npos || start == std::string::npos) return false;
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256(source.data() + start, (CC_LONG)(source.size() - start), digest);
    char hex[CC_SHA256_DIGEST_LENGTH * 2 + 1];
    const char* digits = "0123456789abcdef";
    for (unsigned n = 0; n < CC_SHA256_DIGEST_LENGTH; ++n) {
        hex[n * 2] = digits[digest[n] >> 4]; hex[n * 2 + 1] = digits[digest[n] & 15];
    }
    hex[sizeof(hex) - 1] = 0;
    if (fingerprint) *fingerprint = hex;
    if (std::strcmp(hex, "95a4b16527bcfbe7d4818bc0e837d88257ecaf9419be0ac694062d7be2080ad6")) return false;
    if (const char* enabled = std::getenv("RDR2_MVK_ROCK_HIZ_BYPASS")) {
        if (std::strcmp(enabled, "1")) return false;
    }
    // Keep the outer HiZ gate and the _m15 bit-0 inversion. Skipping the
    // whole block admits geometry to both normal and inverted passes.
    const char* depthBranch = "if (_510)";
    auto depthPos = source.find(depthBranch, pos + std::strlen(branch));
    if (depthPos == std::string::npos) return false;
    source.replace(depthPos, std::strlen(depthBranch),
                   "if (false) // RDR2 depth-only bypass; preserve pass inversion");
    return true;
}
