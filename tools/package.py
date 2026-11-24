# SPDX-License-Identifier: MIT
"""Package the Windows x64 Nintendo DS firmware player."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DLLS = ("SDL3.dll", "libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll")


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


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
    for filename in (*DLLS, "libiconv-2.dll"):
        files["runtime/" + filename] = args.toolchain_bin / filename
    assets = args.launcher / "assets"
    for path in sorted(assets.rglob("*")):
        if path.is_file():
            files["assets/" + path.relative_to(assets).as_posix()] = path
    metadata = dict(version="0.1.0", boot="firmware", source=revision(ROOT),
                    ndsrecomp=revision(engine), recomp_ui=revision(ROOT / "recomp-ui"),
                    files={name: sha256(path) for name, path in files.items()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "x", zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for name, path in files.items():
            archive.write(path, name)
        archive.writestr("build.json", json.dumps(metadata, indent=2) + "\n")
    with zipfile.ZipFile(args.out) as archive:
        if archive.testzip() is not None:
            raise ValueError("Package integrity check failed")
    print(f"{sha256(args.out)}  {args.out}")


if __name__ == "__main__":
    main()
