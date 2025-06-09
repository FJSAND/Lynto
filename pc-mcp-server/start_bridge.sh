#!/bin/bash

# MCP网络桥接服务启动脚本
# 用于在Mac/PC上启动MCP服务，供iOS设备连接

set -e

# 配置参数
BRIDGE_PORT=${BRIDGE_PORT:-8765}
SERVICE_NAME=${SERVICE_NAME:-"MCP-Bridge-Service"}
MCP_SERVER=${MCP_SERVER:-"python3 example_mcp_server.py"}

echo "🚀 启动MCP网络桥接服务..."
echo "📋 配置信息:"
echo "   - 服务名称: $SERVICE_NAME"
echo "   - WebSocket端口: $BRIDGE_PORT"
echo "   - MCP服务器: $MCP_SERVER"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3.7+."
    exit 1
fi

# 检查当前目录
if [ ! -f "mcp_network_bridge.py" ]; then
    echo "❌ 错误: 未找到mcp_network_bridge.py，请确保在正确的目录中运行."
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -f ".deps_installed" ]; then
    echo "📦 首次运行，安装依赖..."
    python3 -m pip install -r requirements.txt
    touch .deps_installed
    echo "✅ 依赖安装完成"
fi

# 创建示例MCP服务器（如果不存在）
if [ ! -f "example_mcp_server.py" ]; then
    echo "📄 创建示例MCP服务器..."
    python3 setup.py
fi

# 检查端口是否被占用
if lsof -Pi :$BRIDGE_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告: 端口 $BRIDGE_PORT 已被占用"
    echo "🔄 尝试杀死占用端口的进程..."
    lsof -ti:$BRIDGE_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动服务
echo "🌐 启动网络桥接服务（端口: $BRIDGE_PORT）..."
echo "💡 提示: 确保你的Mac和iPhone在同一个局域网内"
echo "📱 iOS设备将能够自动发现此服务"
echo ""
echo "🛑 按 Ctrl+C 停止服务"
echo "----------------------------------------"

# 启动MCP网络桥接
python3 mcp_network_bridge.py \
    --port $BRIDGE_PORT \
    --service-name "$SERVICE_NAME" \
    --mcp-command "$MCP_SERVER" 