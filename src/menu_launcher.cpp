// SPDX-License-Identifier: MIT
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

extern "C" {
#include "launcher_files.h"
}
#include "launcher_profile.h"
#include "recomp_launcher.h"
#include "sha256.h"

#include <array>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string_view>

namespace fs = std::filesystem;

namespace {
struct BiosInput {
    const char* filename;
    const char* label;
    size_t length;
    const char* sha256;
};

constexpr BiosInput arm7{"biosnds7.rom", "Nintendo DS ARM7 BIOS", 16384,
    "ba65f690eb04ec92db67c0e299e21ad71de087d6d5de8a9cb17a62eaab563c17"};
constexpr BiosInput arm9{"biosnds9.rom", "Nintendo DS ARM9 BIOS", 4096,
    "1693983a7707ae394786fa526c0552457888a51d4e410d715ef07acd5a540555"};

bool bios_matches(const fs::path& path, const BiosInput& input) {
    std::ifstream file(path, std::ios::binary);
    std::array<uint8_t, 16384> bytes{};
    if (!file.read(reinterpret_cast<char*>(bytes.data()), input.length) ||
        file.peek() != std::char_traits<char>::eof()) return false;
    std::array<uint8_t, 32> digest{};
    std::array<char, 65> hex{};
    recompui_sha256_compute(bytes.data(), input.length, digest.data());
    for (size_t i = 0; i < digest.size(); ++i) {
        std::snprintf(hex.data() + 2 * i, 3, "%02x", static_cast<unsigned>(digest[i]));
    }
    return std::string_view(hex.data()) == input.sha256;
}

fs::path select_bios(const fs::path& firmware, const std::string& remembered,
                     const BiosInput& input) {
    const auto nearby = firmware.parent_path() / input.filename;
    if (bios_matches(nearby, input)) return nearby;
    const auto prior = fs::u8path(remembered);
    if (bios_matches(prior, input)) return prior;

    const char* patterns[] = {"*.rom", "*.bin"};
    const auto title = std::string("Select the ") + input.label;
    char path[2048]{};
    if (!launcher_pick_file(title.c_str(), patterns, 2, input.label, path, sizeof path)) return {};
    const auto selected = fs::absolute(fs::u8path(path));
    if (!bios_matches(selected, input)) {
        throw std::runtime_error(std::string("The selected file is not the supported ") + input.label);
    }
    return selected;
}

int read_firmware(void*, const char* path, uint8_t** bytes, size_t* size,
                  char* error, size_t error_size) {
    std::ifstream file(fs::u8path(path), std::ios::binary | std::ios::ate);
    const auto length = file.tellg();
    if (length != 0x20000 && length != 0x40000) {
        std::snprintf(error, error_size, "Choose an original 128 or 256 KiB firmware dump.");
        return 0;
    }
    *size = static_cast<size_t>(length);
    *bytes = static_cast<uint8_t*>(std::malloc(*size));
    if (!*bytes) return 0;
    file.seekg(0);
    return file.read(reinterpret_cast<char*>(*bytes), length) ? 1 : 0;
}

void free_firmware(void*, uint8_t* bytes) {
    std::free(bytes);
}

int boot(const fs::path& root, const fs::path& firmware, const fs::path& bios7,
         const fs::path& bios9) {
    const auto runtime = root / "runtime" / "nds_runner.exe";
    const auto state = root / "firmware-state.bin";
    std::wstring command = L"\"" + runtime.native() + L"\" --interactive --boot firmware"
        L" --firmware-path \"" + firmware.native() + L"\" --bios7-path \"" + bios7.native() +
        L"\" --bios9-path \"" + bios9.native() + L"\" --firmware-state-path \"" + state.native() + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    if (!CreateProcessW(runtime.c_str(), command.data(), nullptr, nullptr, FALSE,
                        CREATE_NO_WINDOW, nullptr, root.c_str(), &startup, &child)) {
        throw std::runtime_error("Could not start the Nintendo DS runtime");
    }
    CloseHandle(child.hThread);
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD result = 2;
    GetExitCodeProcess(child.hProcess, &result);
    CloseHandle(child.hProcess);
    return static_cast<int>(result);
}
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    try {
        std::wstring executable(32768, L'\0');
        const DWORD length = GetModuleFileNameW(nullptr, executable.data(), static_cast<DWORD>(executable.size()));
        if (!length || length == executable.size()) return 2;
        executable.resize(length);
        const auto root = fs::path(executable).parent_path();
        const auto preference = root / "menu-inputs.cfg";
        std::string last, last_bios7, last_bios9;
        std::ifstream config(preference);
        std::getline(config, last);
        std::getline(config, last_bios7);
        std::getline(config, last_bios9);

        RecompLauncherCSettings settings{};
        settings.window_scale = 2;
        settings.enable_audio = 1;
        settings.audio_freq = 48000;
        settings.volume = 100;
        RecompLauncherCGameInfo game{};
        launcher_profile_apply("nds", &game);
        static const char* patterns[] = {"*.bin", "*.rom"};
        game.name = "Nintendo DS Menu";
        game.rom_noun = "firmware";
        game.rom_filter_desc = "Nintendo DS firmware";
        game.rom_patterns = patterns;
        game.num_rom_patterns = 2;
        game.rom_read = read_firmware;
        game.rom_read_free = free_firmware;
        game.has_bios = 0;
        game.setup_wizard_supported = 1;
        char selected[2048]{};
        const auto assets = (root / "assets").u8string();
        const int result = recomp_launcher_run_window("Nintendo DS Menu", &settings, &game,
            assets.c_str(), last.c_str(), selected, sizeof selected);
        if (result == RECOMP_LAUNCHER_RESULT_QUIT) return 0;
        if (result != RECOMP_LAUNCHER_RESULT_LAUNCH || !selected[0]) return 2;

        const auto firmware = fs::absolute(fs::u8path(selected));
        const auto bios7 = select_bios(firmware, last_bios7, arm7);
        if (bios7.empty()) return 0;
        const auto bios9 = select_bios(firmware, last_bios9, arm9);
        if (bios9.empty()) return 0;
        std::ofstream(preference) << firmware.u8string() << '\n' << bios7.u8string()
                                  << '\n' << bios9.u8string() << '\n';
        return boot(root, firmware, bios7, bios9);
    } catch (const std::exception& error) {
        MessageBoxA(nullptr, error.what(), "Nintendo DS Menu", MB_OK | MB_ICONERROR);
        return 2;
    }
}
