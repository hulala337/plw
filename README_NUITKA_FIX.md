# V3.2.3 Windows 打包修复说明

你在 V3.2.1/V3.2.2 使用 Nuitka 4.2.1 + pywebview 时遇到的错误：

`FATAL: pywebview: Conflict between user and plugin decision for module 'webview.platforms.cocoa'`

不是你的业务代码错误，而是 Nuitka 4.2.1 的 pywebview 平台模块决策与当前打包路径发生冲突。Nuitka 4.2 确实加入了 pywebview 平台自动处理，但你的实际组合仍会在分析阶段失败。

V3.2.3 因此把**默认 Windows 发布引擎切换为 PyInstaller one-file**。pywebview 官方 Windows/Linux 冻结文档本身推荐 PyInstaller；同时 spec 明确排除 Android/Cocoa/GTK/Qt 等非 Windows backend，只保留 Windows backend。

这不会删除 V3.2 的安全机制：Ed25519 资源清单仍在构建时签名，程序启动时继续验证版权信息、作者信息和微信收款码等受保护资源。

## 使用

直接双击：

`build_release.bat`

输出：

`release\\PelicanWorkbench_Setup_3.2.3.exe`

## 为什么暂时不强行修 Nuitka

Nuitka Standard 对 Python 代码的逆向门槛通常高于 PyInstaller，但当前版本首先要保证 Windows 产品能够稳定构建和运行。正式商业发布时，可以再单独建立一条经过 Windows 实机验证的 Nuitka 构建链；不要让发布链依赖一个会在 pywebview 分析阶段直接 FATAL 的组合。
