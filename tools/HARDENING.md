# Pelican Workbench V3.2 加固说明

这套加固目标不是“绝对不可破解”（离线 Windows 软件无法做到），而是显著提高修改版权、收款码、前端资源和二次打包的成本，并让普通用户更容易识别被修改的版本。

## 1. Nuitka 编译

正式发布默认使用 Nuitka，把 Python 代码编译成本机二进制，再制作 onefile EXE。相比直接分发 `.py/.pyc`，反编译门槛更高。

## 2. 签名完整性清单

发布时生成 Ed25519 签名，保护：

- `web/index.html`
- `web/assets/app.js`
- `web/assets/style.css`
- `web/assets/wechat_qr.png`

程序启动时验证签名和 SHA-256。若发布包中的品牌、二维码或前端资源被直接修改，程序会拒绝启动。

**私钥绝对不要放进源码压缩包。** 构建脚本默认把私钥放在用户目录下的 `.pelican_workbench/signing/private.key`。

## 3. Authenticode（强烈推荐）

如果有代码签名证书，可在构建脚本中提供 `PFX_PATH`、`PFX_PASSWORD`、`SIGNTOOL_PATH` 和可选的 `TIMESTAMP_URL`，对最终 EXE 与安装器签名。

这样用户在 Windows 文件属性里可以看到数字签名；被修改过的 EXE 会失去原签名。

## 4. 现实边界

熟练的逆向人员仍可能通过 patch、调试或修改启动逻辑绕过离线完整性检查。若要进一步降低风险，可把版本校验/作者信息放到在线服务，并在发布服务器端提供签名版本清单。不过这会牺牲“完全离线”的产品特性，应当作为可选的在线增强，而不是强制依赖。
