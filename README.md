# OpenSight 3.1

OpenSight 是一款安全优先、本地运行、便携版 Windows x64 OpenVPN 节点质量评估与连接管理工具。OpenVPN 与 sing-box 用户态运行时内置；Windows VPN 驱动和应用分流 TUN 虚拟网卡在首次需要时可能需要一次管理员授权。

## 核心设计原则
1. **完全自包含便携 (Fully Self-Contained Portable):** 最终发布包内嵌经过官方源 SHA-256 校验的真实 OpenVPN 与 sing-box 运行时组件，OpenSight、OpenVPN 用户态运行时与 sing-box 运行时均内置；Windows VPN 驱动属于系统级组件，首次使用时可能需要一次管理员确认。
2. **安全测速模式 (Safe Measurement Mode):** 节点探测全程基于原生 TCP Socket 测量，**绝不建立 VPN 隧道，不改变公网 IP**。
3. **真实可执行文件与严格安全门禁:** 构建流水线保证真实产物交付，全流程杜绝伪造二进制与虚拟 Stub。若任何组件下载、签名校验、哈希校验或运行时检查失败，构建立即阻断。

---

## 本地构建与验证说明

### 1. 初始化虚拟环境
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2. 运行全量单元测试与反伪造审计
```powershell
pytest -q
```

### 3. 构建应用并下载校验真实运行时组件
```powershell
python scripts/build_portable.py
python scripts/fetch_components.py --dest dist/OpenSight
```

### 4. 首次使用 OpenVPN（如 Windows 尚无驱动）
首次安装/修复时在“设置”页面点击按钮，软件会先解释原因，再弹出 Windows 管理员授权。

### 4. 执行真实 QML 启动冒烟测试
```powershell
python scripts/smoke_test.py dist/OpenSight/OpenSight.exe
```

### 5. 封装便携式发布包与清单校验
```powershell
python scripts/package_release.py --commit LOCAL_BUILD
python scripts/verify_manifest.py dist/staging
python scripts/verify_provenance.py dist/staging
```