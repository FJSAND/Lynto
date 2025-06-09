# 灵拓 Lynto - 官方网站 & MCP 服务器

这是灵拓 Lynto iOS 应用的官方网站代码仓库，同时包含配套的 MCP (Model Context Protocol) 服务器。

## 📱 关于灵拓 Lynto

灵拓 Lynto 是一款创新的 AI 聊天应用，专为 iPhone 和 iPad 设计，集成了先进的 DeepSeek AI 和 Model Context Protocol (MCP) 技术。
### 🔗 下载链接

**[从 App Store 下载灵拓 Lynto](https://apps.apple.com/cn/app/%E7%81%B5%E6%8B%93-mcp%E6%9C%8D%E5%8A%A1%E5%AE%9E%E7%8E%B0/id6746976836)**

### ⚡ SSE 服务特性

**便捷的内置 SSE 服务**：应用内已经集成了多种 SSE (Server-Sent Events) 服务，您只需添加相应服务的 Token 就能立即获取相应的 AI 能力和功能扩展，无需复杂配置，即开即用。

## 🌐 网站功能

- **现代化响应式设计** - 完美适配各种设备屏幕
- **产品介绍** - 详细的功能特性展示
- **隐私政策** - 完整的用户隐私保护说明
- **技术栈展示** - 展示使用的先进技术
- **联系方式** - 便捷的用户反馈渠道

## 🔧 MCP 服务器

本仓库还包含一套完整的 MCP 服务器实现，为灵拓 Lynto 应用提供扩展功能支持。

## 🚀 快速开始

### 网站部署

1. 克隆仓库：
```bash
git clone https://github.com/FJSAND/Lynto.git
cd Lynto
```

2. 使用本地服务器预览：
```bash
# 使用 Python
python -m http.server 8000

# 或使用 Node.js
npx serve .
```

3. 访问 `http://localhost:8000`

### MCP 服务器部署

1. 进入 MCP 服务器目录：
```bash
cd pc-mcp-server
```

2. 创建虚拟环境：
```bash
python3 -m venv mcp_env
source mcp_env/bin/activate  # macOS/Linux
# 或在 Windows: mcp_env\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置 MCP 服务器（编辑 `mcp_servers.json`）：
```json
{
  "servers": {
    "amap": {
      "name": "高德地图",
      "description": "高德地图API服务：地理编码、路径规划、POI搜索等",
      "command": ["npx", "-y", "@amap/amap-maps-mcp-server"],
      "env": {
        "AMAP_MAPS_API_KEY": "your-api-key"
      },
      "prefix": "amap"
    },
    "official": {
      "name": "官方示例",
      "description": "官方MCP示例服务器：echo、add、time工具",
      "command": ["python3", "official_mcp_server.py", "--mode", "stdio"],
      "env": {},
      "prefix": "demo"
    }
  },
  "gateway": {
    "port": 8765,
    "host": "0.0.0.0",
    "name": "MCP统一网关",
    "version": "1.0.0"
  }
}
```

5. 启动 MCP 网关服务：
```bash
source mcp_env/bin/activate
python3 mcp_gateway.py --debug
```

## 📁 文件结构

```
.
├── index.html              # 主页面
├── privacy.html            # 隐私政策页面
├── styles.css              # 样式文件
├── script.js               # 交互脚本
├── README.md              # 项目说明
└── pc-mcp-server/         # MCP 服务器
    ├── mcp_gateway.py     # MCP 网关主程序
    ├── mcp_servers.json   # 服务器配置文件
    ├── requirements.txt   # Python 依赖
    ├── official_mcp_server.py    # 官方示例服务器
    ├── amap_mcp_bridge.py        # 高德地图桥接服务
    ├── simple_mcp_bridge.py      # 简单桥接实现
    ├── mcp_network_bridge.py     # 网络桥接服务
    ├── example_mcp_server.py     # 示例MCP服务器
    ├── setup.py               # 安装脚本
    └── start_bridge.sh        # 启动脚本
```

## 🌟 在线访问

网站已部署在 GitHub Pages：
**https://fjsand.github.io/Lynto/**

## 🔧 MCP 服务器详细说明

### 功能特性

- **🌐 统一网关** - 通过 WebSocket 提供统一的 MCP 服务接口
- **🔌 多服务器支持** - 同时管理多个 MCP 服务器实例
- **⚙️ 配置管理** - 通过 JSON 文件简化服务器配置
- **🛠️ 调试模式** - 详细的日志输出，便于开发调试
- **🔄 自动重连** - 服务器异常时自动重启机制

### 配置说明

编辑 `pc-mcp-server/mcp_servers.json` 文件来配置 MCP 服务器：

- **servers**: 定义各个 MCP 服务器的配置
  - **name**: 服务器显示名称
  - **description**: 服务器功能描述
  - **command**: 启动命令数组
  - **env**: 环境变量设置
  - **prefix**: 工具命名前缀

- **gateway**: 网关服务配置
  - **port**: WebSocket 服务端口（默认 8765）
  - **host**: 绑定地址（默认 0.0.0.0）

### 使用示例

1. **启动服务**：
```bash
cd pc-mcp-server
source mcp_env/bin/activate
python3 mcp_gateway.py --debug
```

2. **连接测试**：
服务启动后，iOS 应用可通过 WebSocket 连接到：
```
ws://localhost:8765
```

3. **添加新服务器**：
在 `mcp_servers.json` 的 servers 段添加新配置：
```json
"your_server": {
  "name": "自定义服务器",
  "description": "您的MCP服务器描述",
  "command": ["python3", "your_server.py"],
  "env": {
    "API_KEY": "your-api-key"
  },
  "prefix": "custom"
}
```

### 故障排除

- **端口被占用**: 修改 `mcp_servers.json` 中的 port 设置
- **服务器启动失败**: 检查 command 路径和 env 环境变量
- **连接超时**: 确认防火墙设置和网络连接

## 📧 联系我们

如有任何问题或建议，请联系：
- 邮箱：fjsand@163.com

## 📄 许可证

本项目仅用于展示灵拓 Lynto 应用信息，版权所有。

---

© 2024 灵拓 Lynto. All rights reserved. 
