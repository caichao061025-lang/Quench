# 🔥 淬火 (Quench)

> **淬火**——锻造刀剑的关键工序。钢材经高温煅烧后急速冷却，方能变得坚硬锋利。
> 正如安全测试之于防御体系：每一次攻击模拟，都是对系统防线的一次淬炼。

**淬火**是一款轻量级 Webshell 管理工具，专为授权渗透测试、CTF 竞赛和安全教学而设计。纯 Python 标准库构建，零外部依赖，开箱即用。

> ⚠️ **郑重声明**：本工具仅供授权的安全测试、CTF 竞赛和安全教育目的使用。严禁用于任何未经授权的入侵或非法活动。使用者须自行承担全部法律责任。

---

## ✨ 为什么叫「淬火」？

锻造一把好刀，离不开「淬火」这道工序——钢材加热到临界温度后急速冷却，内部晶格重新排列，硬度与韧性同时跃升。

渗透测试的使命与此如出一辙：在高强度攻防对抗中暴露系统的薄弱环节，迫使防御者在一次次「淬炼」中加固防线。**淬火不是为了毁灭，而是为了更强。**

---

## 🧰 功能一览

| 模块 | 功能 |
|------|------|
| 📁 **文件管理** | 浏览、上传、下载、编辑、删除、重命名、修改权限、修改时间戳 |
| 💻 **远程终端** | 交互式命令执行，支持命令历史 |
| 🗄 **数据库管理** | 连接 MySQL/MariaDB，执行 SQL 查询，查看结果 |
| 🔐 **加密传输** | XOR + Base64 双重编码，避免明文暴露 |
| 📋 **多目标管理** | 同时管理多个 Webshell 连接，配置持久化到本地 |

---

## 📂 项目结构

```
Quench/
├── webshell/
│   └── shell.php              # PHP Webshell（部署到靶机）
├── client/
│   ├── main.py                # 客户端入口
│   ├── core/
│   │   ├── encoder.py         # XOR + Base64 编解码器
│   │   ├── connector.py       # HTTP 通信层
│   │   └── shell_manager.py   # 多 Shell 配置管理
│   └── ui/
│       ├── main_window.py     # 主窗口
│       ├── file_manager.py    # 文件管理面板
│       ├── terminal.py        # 终端面板
│       ├── database.py        # 数据库面板
│       └── theme.py           # UI 主题
├── Quench.exe                 # 打包好的 Windows 客户端
└── README.md
```

---

## 🚀 快速开始

### 环境要求

| 角色 | 要求 |
|------|------|
| **服务端（靶机）** | PHP 5.6+，数据库功能需要 `mysqli` 或 `PDO` 扩展 |
| **客户端** | Python 3.7+（仅标准库，无需 pip 安装任何包）或直接运行 `Quench.exe` |

### 第一步：部署 Webshell

将 `webshell/shell.php` 上传到目标 Web 服务器的可访问目录。

本地测试可用 PHP 内置服务器快速搭建：

```bash
cd webshell
php -S 127.0.0.1:8080
# Webshell 地址: http://127.0.0.1:8080/shell.php
```

> 🔐 部署前务必修改 `shell.php` 中的 `$PASSWORD` 变量（默认值：`test`）

### 第二步：启动客户端

**方式一：直接运行 EXE（推荐 Windows 用户）**

双击 `Quench.exe`，配置信息自动保存在同目录下的 `config.json`。

**方式二：Python 源码运行**

```bash
cd client
python main.py
```

### 第三步：添加连接

1. 点击左侧 **＋ 添加** 按钮
2. 填写连接信息：
   - **名称**：任意标识，如 `本地靶机`
   - **URL**：Webshell 地址，如 `http://127.0.0.1:8080/shell.php`
   - **密码**：与 `shell.php` 中的 `$PASSWORD` 一致
3. 点击保存

### 第四步：开始操作

选中左侧 Shell 列表中的目标即可自动连接，通过顶部标签页切换功能：

- 🗂 **文件管理** → 浏览、上传、编辑远程文件
- ⌨ **终端** → 执行系统命令
- 🗃 **数据库** → 连接并查询数据库

---

## 📦 打包为 EXE

```bash
pip install pyinstaller
cd client
pyinstaller --onefile --windowed --name "Quench" --clean main.py
```

生成文件位于 `client/dist/Quench.exe`。

| 参数 | 作用 |
|------|------|
| `--onefile` | 所有依赖合并为单个 EXE |
| `--windowed` | 隐藏终端窗口，仅显示 GUI |
| `--name` | 输出文件名 |
| `--clean` | 清理构建缓存 |

---

## 🔗 通信协议

```
客户端 (Quench)                           Webshell (PHP)
    │                                          │
    │  ① 构建命令 JSON                          │
    │  {"action":"list","path":"/var/www"}     │
    │                                          │
    │  ② XOR 加密（密钥 = MD5(password)）       │
    │                                          │
    │  ③ Base64 编码                            │
    │                                          │
    │  ④ HTTP POST ────────────────────────►   │
    │     Body: data=<encoded_string>          │
    │                                          │
    │                              ⑤ Base64 解码 │
    │                              ⑥ XOR 解密    │
    │                              ⑦ 执行命令    │
    │                              ⑧ XOR 加密结果 │
    │                              ⑨ Base64 编码 │
    │                                          │
    │  ⑩ Base64 解码 ◄──────────────────────   │
    │  ⑪ XOR 解密                               │
    │  ⑫ 解析并显示结果                         │
```

---

## 📡 支持的命令

| 命令 | 功能 |
|------|------|
| `ping` | 连接测试，返回服务器时间 |
| `info` | 获取系统信息（OS、PHP 版本、当前目录） |
| `list` | 列出目录内容 |
| `read` | 读取文件内容 |
| `write` | 写入/创建文件 |
| `delete` | 删除文件或目录 |
| `rename` | 重命名 |
| `chmod` | 修改权限 |
| `touch` | 修改时间戳 |
| `upload` | 上传文件（Base64 编码传输） |
| `exec` | 执行任意系统命令 |
| `db_query` | 执行数据库查询 |

---

## 🛡 安全建议

1. **修改默认密码** — 部署 `shell.php` 前务必修改 `$PASSWORD`
2. **IP 白名单** — 可在 `shell.php` 中添加来源 IP 限制
3. **启用 HTTPS** — 生产环境使用 TLS 加密传输
4. **用完即删** — 测试完毕后立即从靶机删除 Webshell 文件
5. **监控日志** — 定期审查 Web 服务器访问日志

---

## 📜 许可

本项目仅用于安全教育和授权测试。使用者须遵守所在地法律法规，并对自身行为负责。
