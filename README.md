# Pelican Workbench V3.6.0

Windows 产品版：鹈鹕工作台 · TF7Z-XY

## 一键发布

1. Windows 安装 Python 3.11/3.12 x64。
2. 安装 Inno Setup 6。
3. 双击 `build_release.bat`。
4. 最终安装包位于 `release\\PelicanWorkbench_Setup_3.6.0.exe`。

构建脚本会创建项目自己的 `.venv`，安装固定版本的 pywebview 与 PyInstaller，执行源码自检与资源完整性检查，生成 one-file EXE，随后调用 Inno Setup。

## 隐私

程序不保存实际键盘输入内容，只统计字符数量；不保存聊天正文、网页正文或文档正文。工作数据库位于 `%LOCALAPPDATA%\\PelicanWorkbench`。

## 安全

正式构建时会在 `%USERPROFILE%\\.pelican_workbench\\signing\\private.key` 创建或复用 Ed25519 私钥。私钥不会进入源码包或安装包。受保护资源包括版权信息、版本、前端资源和微信收款码；程序启动时会进行完整性验证。

注意：任何离线 Windows EXE 都不能做到绝对不可逆向。完整性校验主要用于发现资源篡改；正式公开发布还应使用 Authenticode 代码签名。
