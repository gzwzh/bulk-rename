import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_ASSETS = ROOT / "build_assets"
ICONSET_DIR = BUILD_ASSETS / "app.iconset"
ICNS_PATH = BUILD_ASSETS / "app_icon.icns"
SOURCE_ICON = ROOT / "app_icon.png"
DIST_DIR = ROOT / "dist_macos"
WORK_DIR = ROOT / "build" / "macos"


def run(cmd):
    print(">", " ".join(str(part) for part in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def ensure_macos():
    if sys.platform != "darwin":
        raise SystemExit("This script must be run on macOS.")


def generate_icns():
    if not SOURCE_ICON.exists():
        raise FileNotFoundError(f"Missing icon source: {SOURCE_ICON}")

    BUILD_ASSETS.mkdir(exist_ok=True)
    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for size, name in sizes:
        run(["sips", "-z", str(size), str(size), str(SOURCE_ICON), "--out", str(ICONSET_DIR / name)])

    run(["iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(ICNS_PATH)])


def build_arch(arch):
    dist_path = DIST_DIR / arch
    work_path = WORK_DIR / arch

    if dist_path.exists():
        shutil.rmtree(dist_path)
    if work_path.exists():
        shutil.rmtree(work_path)

    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist_path),
        "--workpath",
        str(work_path),
        "macos_build.spec",
    ])


def main():
    parser = argparse.ArgumentParser(description="Build macOS app bundles for this project.")
    parser.add_argument("--arch", choices=["arm64", "x86_64", "both"], default="both")
    args = parser.parse_args()

    ensure_macos()
    generate_icns()

    arches = ["arm64", "x86_64"] if args.arch == "both" else [args.arch]
    for arch in arches:
        build_arch(arch)


if __name__ == "__main__":
    main()
