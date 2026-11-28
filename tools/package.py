# SPDX-License-Identifier: MIT
"""Package the Windows x64 Nintendo DS firmware player."""

import argparse
import json
from pathlib import Path
import re
import subprocess


import os
import sys
sys.path.insert(0, str(Path(os.environ.get("NDSRECOMP_ROOT", Path(__file__).resolve().parents[1] / "ndsrecomp")) / "tools"))
from nds_tools.release import sha256, write_archive, check_pe_dependencies, runtime_dll_files

ROOT = Path(__file__).resolve().parents[1]
DLLS = ("SDL3.dll", "libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll")



def revision(path):
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--toolchain-bin", type=Path, default=Path("C:/msys64/mingw64/bin"))
    args = parser.parse_args()
    runtime = args.runtime / "nds_runner.exe"
    report = subprocess.check_output(
        [args.toolchain_bin / "objdump.exe", "-f", "-p", runtime], text=True
    )
    imports = re.findall(r"DLL Name:\s*(\S+)", report, re.IGNORECASE)
    if "pei-x86-64" not in report.lower() or not set(DLLS).issubset(imports):
        raise ValueError("Expected the Windows x64 SDL3 firmware runtime")

    engine = ROOT / "ndsrecomp"
    files = {
        "NintendoDSMenu.exe": args.launcher / "NintendoDSMenu.exe",
        "runtime/nds_runner.exe": runtime,
        "README.md": ROOT / "SETUP.md",
        "LICENSE": ROOT / "LICENSE",
        "licenses/ndsrecomp-LICENSE": engine / "LICENSE",
        "licenses/GPL-3.0.txt": engine / "LICENSE-GPL",
        "licenses/ndsrecomp-MIT.txt": engine / "LICENSE-MIT",
        "licenses/THIRD_PARTY_ATTRIBUTION.md": engine / "THIRD_PARTY_ATTRIBUTION.md",
        "licenses/recomp-ui-LICENSE": ROOT / "recomp-ui/LICENSE",
        "licenses/imgui-LICENSE.txt": ROOT / "recomp-ui/src/third_party/imgui/LICENSE.txt",
        "licenses/SDL3-LICENSE.txt": args.toolchain_bin.parent / "share/licenses/SDL3/LICENSE.txt",
        "licenses/MinGW-GCC-COPYING3": args.toolchain_bin.parent / "share/licenses/gcc-libs/COPYING3",
        "licenses/MinGW-GCC-RUNTIME": args.toolchain_bin.parent / "share/licenses/gcc-libs/COPYING.RUNTIME",
        "licenses/winpthread-COPYING": args.toolchain_bin.parent / "share/licenses/libwinpthread/COPYING",
        "licenses/libiconv-COPYING.LIB": args.toolchain_bin.parent / "share/licenses/libiconv/COPYING.LIB",
    }
    for filename, source in runtime_dll_files(args.toolchain_bin, ("SDL3",)).items():
        files["runtime/" + filename] = source
    assets = args.launcher / "assets"
    for path in sorted(assets.rglob("*")):
        if path.is_file():
            files["assets/" + path.relative_to(assets).as_posix()] = path
    metadata = dict(version="0.1.0", boot="firmware", source=revision(ROOT),
                    ndsrecomp=revision(engine), recomp_ui=revision(ROOT / "recomp-ui"),
                    files={name: sha256(path) for name, path in files.items()})
    check_pe_dependencies(files, args.toolchain_bin / "objdump.exe")
    write_archive(args.out, files, {"build.json": json.dumps(metadata, indent=2) + "\n"})
    print(f"{sha256(args.out)}  {args.out}")


if __name__ == "__main__":
    main()
