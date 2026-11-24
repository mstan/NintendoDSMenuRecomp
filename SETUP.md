# Nintendo DS Menu Recomp

Standalone consumer for the original Nintendo DS firmware menu. The shared runtime, BIOS profiles and recompiler are supplied by the [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp) submodule.

## Windows x64

Extract the release and run `NintendoDSMenu.exe`. In recomp-ui, select your
original Nintendo DS firmware dump and choose **Play**. The launcher looks for
`biosnds7.rom` and `biosnds9.rom` beside the firmware, then opens a picker for
any missing BIOS. The Windows build was checked with the retail BIOS pair and
a 256 KiB firmware dump.

The HLE loader starts the two original firmware programs in RAM. The DS menu
opens with an empty cartridge slot. Keep `firmware-state.bin` when updating
the player to retain local firmware settings. The original dumps stay read-only.

## Build

Initialize the engine and recomp-ui submodules. Use Release builds of this
repo's `NintendoDSMenu` target and ndsrecomp's `nds_runner` target with SDL3.
Prepare the BIOS dispatch banks from your own dumps using the engine tools
and pass the directory via `NDS_GENERATED_DIR`.
Set `NDS_BOOTSTRAP_FIRMWARE=ON` for the Windows package and use
`tools/package.py` to combine the two build directories.

The supported BIOS identities and the firmware used for validation are
recorded in `inputs.toml`.

```powershell
git submodule update --init --recursive
python tools/verify_inputs.py path/to/biosnds7.rom path/to/biosnds9.rom path/to/firmware.bin
```
