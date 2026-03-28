# Linux 版本打包指南

本指南将指导你如何从 Windows 环境下，使用 Docker 技术将本项目打包成 Linux 可执行文件。

## 前置条件

1.  **安装 Docker Desktop**：确保你的 Windows 上已安装并运行 Docker。
2.  **网络连接**：Docker 需要从互联网下载基础镜像和依赖包。

## 打包步骤

1.  **打开命令行工具**：
    在项目根目录（`bulk_rename_tool`）下打开 PowerShell 或 CMD。

2.  **构建 Docker 镜像**：
    运行以下命令构建用于打包的 Linux 环境：
    ```bash
    docker build -t bulk-rename-builder -f Dockerfile.linux .
    ```

3.  **执行打包并导出文件**：
    运行以下命令将打包好的 Linux 文件导出到你的 Windows `dist` 目录中：
    ```bash
    docker run --rm -v ${PWD}:/app bulk-rename-builder
    ```
    *注：如果是使用 CMD，请将 `${PWD}` 替换为 `%cd%`。*

4.  **查找输出文件**：
    打包完成后，你会在 `dist` 目录下看到一个名为 `bulk_rename` 的二进制文件。

## 如何运行 Linux 版本

在 Linux 系统上（如 Ubuntu）：

1.  赋予执行权限：
    ```bash
    chmod +x bulk_rename
    ```
2.  运行程序：
    ```bash
    ./bulk_rename
    ```

## 注意事项

-   打包过程中会下载 Ubuntu 镜像及 Python 运行环境，初次构建可能需要几分钟。
-   `linux_build.spec` 专门为 Linux 环境配置，不会干扰 Windows 版本的打包脚本。
-   Linux 版本已包含基础的 Qt 运行库，但如果目标 Linux 系统过于精简，可能需要手动安装一些系统依赖（如 `libxcb` 系列）。
