<div align="center">

# 🌐 OpenSight 3.1
### 智能 VPN 节点质量评估与应用级路由管理系统
**安全优先 · 零信任配置解析 · 进程级分流 · 本地自包含便携版**

[![Windows](https://img.shields.io/badge/Platform-Windows%20x64-blue.svg?logo=windows)]()
[![Rust](https://img.shields.io/badge/Frontend-Tauri%20v2%20%7C%20React%2018-orange.svg?logo=rust)]()
[![Python](https://img.shields.io/badge/Core-FastAPI%20%7C%20Python%203.11+-brightgreen.svg?logo=python)]()
[![Security](https://img.shields.io/badge/Security-DPAPI%20%7C%20Fail--Closed%20KillSwitch-red.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

[功能特性](#-功能特性) • [安全与架构](#-架构设计-architecture) • [快速开始](#-快速开始与使用指南-getting-started) • [本地构建](#-开发者与构建指南-developer-guide) • [常见问题 (FAQ)](#-常见问题与故障排除-faq)

</div>

---

## 📖 项目简介 (Introduction)

**OpenSight** 是一款面向 Windows 平台的下一代、高安全性 VPN 节点评估与多模式连接管理工具。

传统的 VPN 客户端往往面临**配置解析 RCE 风险**、**全局网络劫持**、**DNS/IPv6 隐蔽泄漏**以及**缺乏客观节点测速**等痛点。OpenSight 采用 **“零建立隧道安全测速”**、**“零信任 AST 配置语法过滤”** 与 **“sing-box 驱动的应用级出站分流”** 核心技术，在完全不泄露本地公网 IP 的前提下，实现毫秒级节点延迟、抖动、网页与视频质量综合评分，并支持指定特定 Windows 进程走代理或直连。

---

## ✨ 核心特性 (Key Features)

### 1. 🔍 智能节点综合评分与安全无感探测
* **安全测速模式 (Zero-Tunnel Safe Probe)**：基于原生底层高并发 TCP Socket 探测，**探测全程绝不建立 VPN 隧道，不改变本地公网 IP 与路由表**，杜绝测速过程中的网络漂移和 IP 暴露。
* **多维度加权评分模型**：
  * 🌐 **网页浏览指数 (Web Score)**：综合 TCP 首包延迟与 TCP 握手 RTT。
  * 🎬 **流媒体指数 (Video Score)**：针对连续数据吞吐与抖动（Jitter）优化打分。
  * 🛡️ **稳定性指数 (Stability Score)**：多轮丢包率与重试抖动分析。
* **网络环境漂移感知**：探测前后动态验证出口 IP 完整性，若底层网络切换立即阻断批次，防止脏数据入库。

### 2. 🛡️ 零信任安全防护与隐私强化
* **零信任 OVPN 配置解析**：
  * 内置 AST 词法状态机解析器，严格过滤并阻断包含恶意 `up`, `down`, `script-security`, `plugin` 等可导致任意命令执行（RCE）的危险配置指令。
  * 深度支持 `<connection>`、`<ca>`、`<key>` 等块作用域分析与防重链接攻击。
* **硬件绑定的凭据加密 (Windows DPAPI)**：
  * VPN 登录账户与凭据持久化时调用 Windows 原生 `CryptProtectData` 加密，异机与未授权账户无法还原。
  * 内存级敏感数据擦除与全局日志脱敏过滤器（`CredentialSanitizer`）。
* **全生命周期原子 KillSwitch 防火墙**：
  * 基于 Windows 高级防火墙（WFP/netsh）实施两阶段事务控制，支持操作失败自动快照回滚。
  * 强制启用 `--block-ipv6` 与 `--redirect-gateway def1 block-local`，彻底杜绝 IPv6 与本地广播泄漏。

### 3. 🔀 精准的应用级进程分流 (Split Tunneling)
* **基于 sing-box 现代内核**：采用高性能 TUN 虚拟网卡驱动，支持进程签名识别。
* **双分流模式自由切换**：
  * **全局代理模式 (Global VPN)**：整机网络流量统一经过 OpenVPN 加密隧道。
  * **进程分流模式 (App-level Routing)**：仅允许用户勾选的指定软件（如 Telegram、浏览器、Git 等）走 VPN，游戏与本地应用直连，互不干扰。
* **Split-DNS 隔离防污染**：代理应用专属 DNS 查询，直连应用直达本地网关，杜绝 DNS 跨域污染。

### 4. 🧰 真正完全自包含便携版 (Zero Dependency)
* 绿色免安装，解压即用。
* 后端采用 Windows 原生 `JobObject` 绑定生命周期，主程序退出或异常闪退时，内核自动清理所有底层进程、临时网络策略与虚拟网卡，**绝不在系统留下残留垃圾**。

---

## 🏗️ 架构设计 (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri v2 前端 (React)                     │
│  - CSP 内容安全策略    - 无危险 eval/innerHTML  - 本地 IPC 隔离  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP Bearer Token + WebSocket
┌──────────────────────────────▼──────────────────────────────┐
│                  FastAPI 本地核心服务 (Python)                 │
│  - 仅绑定 127.0.0.1  - Windows JobObject 生命周期绑定 - CORS 限制 │
├──────────────────────────────┬──────────────────────────────┤
│  凭据管理 (DPAPI + 脱敏)      │  配置解析 (AST 白名单 + 块解析) │
├──────────────────────────────┼──────────────────────────────┤
│  防泄漏与 KillSwitch 防火墙   │  Split-DNS 隔离 (Sing-box)   │
├──────────────────────────────┼──────────────────────────────┤
│  路径安全 (防目录遍历/Junction)│  测速安全 (IP 防漂移 + 速率控制) │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🚀 快速开始与使用指南 (Getting Started)

### 1. 下载与运行
1. 前往本仓库的 [Releases 页面](../../releases) 下载最新版的 `OpenSight-v3.1.0-win-x64-portable-full.zip`。
2. 解压到任意目录（建议路径不含特殊字符）。
3. 双击运行 `OpenSight.exe` 即可启动。

> **💡 关于 Windows SmartScreen 提示：**  
> 由于本项目为开源无商业付费签名的可执行文件，初次运行时 Windows Defender 可能会弹出 *“Windows 已保护你的电脑”* 提示。请放心点击 **【更多信息】-> 【仍要运行】**。本项目代码 100% 开源透明。

### 2. 导入配置与连接
1. **添加配置**：点击顶部栏的【打开配置文件夹】，将你的 `.ovpn` 配置文件拷贝至打开的目录中，点击【刷新导入】。
2. **凭据设置**：如果你的节点需要账号密码验证，点击【凭据设置】填入并保存（数据由 Windows DPAPI 加密存储）。
3. **一键测速**：点击【开始测速】，系统会自动对所有节点进行并发质量诊断并按评分降序排列。
4. **发起连接**：在节点卡片上点击【连接】，选择 **全局模式** 或 **分流模式** 即可开始使用。

---

## 🛠️ 开发者与构建指南 (Developer Guide)

如果你希望在本地从源码构建项目：

### 前置要求
- Windows 10/11 x64
- [Python 3.11+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/) 与 [Rust 工具链](https://rustup.rs/) (用于 Tauri 构建)

### 1. 准备 Python 虚拟环境与依赖
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2. 运行自动化测试与安全校验
```powershell
pytest -q
```

### 3. 拉取官方验证二进制组件与构建
```powershell
# 自动拉取通过 SHA-256 校验的官方 OpenVPN 与 sing-box 运行时
python scripts/fetch_components.py --dest dist/OpenSight

# 执行便携式构建与冒烟测试
python scripts/build_portable.py
python scripts/smoke_test.py dist/OpenSight/OpenSight.exe
```

---

## ❓ 常见问题与故障排除 (FAQ)

<details>
<summary><b>Q1: 为什么点击连接提示虚拟网卡或驱动未就绪？</b></summary>
A: OpenVPN 与应用分流需要 Windows TAP/TUN 虚拟网络适配器支持。请前往 OpenSight 的【设置】面板，点击【安装/修复 OpenVPN 驱动】，授权管理员权限后即可自动静默完成修复。
</details>

<details>
<summary><b>Q2: 分流模式与全局模式有什么区别？</b></summary>
A: 
- <b>全局模式</b>：整机所有应用的数据均通过 OpenVPN 隧道加密传输。
- <b>分流模式</b>：利用 sing-box 高性能内核接管，仅在【应用路由】列表中勾选并设置为“VPN”的软件才会走代理，其余应用直连本地网络，极大节省带宽并降低游戏/办公延迟。
</details>

<details>
<summary><b>Q3: 测速会消耗大量流量吗？</b></summary>
A: 不会。OpenSight 采用安全轻量探测算法，单次测速仅建立极小握手与往返包校验，不会进行几十兆的大文件消耗性测速。
</details>

---

## 📄 开源许可证 (License)

本项目基于 [MIT License](LICENSE) 开源发布。
