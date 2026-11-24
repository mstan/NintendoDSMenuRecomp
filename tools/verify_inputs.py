# SPDX-License-Identifier: MIT
"""Validate the pinned engine's documented original DS menu inputs."""

import argparse
import hashlib
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("arm7_bios", "arm9_bios", "firmware"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    with (ROOT / "inputs.toml").open("rb") as config:
        inputs = tomllib.load(config)
    for name, identity in inputs.items():
        path = getattr(args, name)
        if not path.is_file() or path.stat().st_size != identity["size"]:
            parser.error(f"{name} requires a {identity['size']}-byte image")
        if hashlib.sha1(path.read_bytes()).hexdigest() != identity["sha1"]:
            parser.error(f"{name} differs from the supported image")
    print("The three original DS images match the pinned menu input profile.")


if __name__ == "__main__":
    main()
