# macOS 双架构打包

这个项目的 macOS 版本使用 `PyInstaller` 打包，应用名固定为 `批量重命名`，图标复用根目录的 `app_icon.png`，构建时自动转换为 `.icns`。

## 环境

建议在 macOS 上使用 Python 3.11：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller
```

## 本地打包

同时构建 Apple Silicon 和 Intel：

```bash
python3 build_macos.py --arch both
```

只构建 Apple Silicon：

```bash
python3 build_macos.py --arch arm64
```

只构建 Intel：

```bash
python3 build_macos.py --arch x86_64
```

输出目录：

```text
dist_macos/
  arm64/批量重命名.app
  x86_64/批量重命名.app
```

## GitHub Actions

仓库工作流会分别在：

- `macos-14` 上构建 `arm64`
- `macos-13` 上构建 `x86_64`

运行完成后会上传两个 zip 构建产物。
