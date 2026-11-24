# Nintendo DS Menu Recomp

Standalone consumer for the original Nintendo DS firmware menu. The shared runtime, BIOS profiles and recompiler are supplied by the [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp) submodule.

## Player build status

The pinned engine exposes two boot modes. Direct boot starts a DS cartridge. The original no-cartridge firmware menu currently boots through the engine's LLE reset path in `runner/src/frontend_config.cpp` and `runner/src/main.cpp`. The player needs a host-native HLE firmware-menu entry point before a binary can be released.

Original ARM7 BIOS, ARM9 BIOS and firmware dumps are separate local inputs. This repo keeps the supported input identities in `inputs.toml`. The engine's [firmware boot reference](ndsrecomp/docs/firmware_boot.md) and [HLE architecture](ndsrecomp/HLE_ARCHITECTURE.md) describe the relevant runtime contracts.

```powershell
git submodule update --init --recursive
python tools/verify_inputs.py path/to/biosnds7.rom path/to/biosnds9.rom path/to/firmware.bin
```
