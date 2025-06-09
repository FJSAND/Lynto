#!/usr/bin/env python3
"""
MCP网络桥接服务安装脚本
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装Python依赖"""
    print("📦 安装Python依赖...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def create_example_server():
    """创建示例MCP服务器"""
    example_server = """#!/usr/bin/env python3
'''
示例MCP服务器
实现一些基本的工具演示
'''

import json
import sys
from typing import Dict, Any

class ExampleMCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "echo",
                "description": "回显输入的文本",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要回显的文本"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "add",
                "description": "计算两个数字的和",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "第一个数字"
                        },
                        "b": {
                            "type": "number", 
                            "description": "第二个数字"
                        }
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "example-mcp-server",
                "version": "1.0.0"
            }
        }
    
    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tools": self.tools
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "echo":
            text = arguments.get("text", "")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Echo: {text}"
                    }
                ]
            }
        elif name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a + b
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{a} + {b} = {result}"
                    }
                ]
            }
        else:
            raise ValueError(f"未知工具: {name}")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            else:
                raise ValueError(f"未支持的方法: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def run(self):
        '''运行MCP服务器'''
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
                
            except EOFError:
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {e}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    server = ExampleMCPServer()
    server.run()
"""
    
    with open("example_mcp_server.py", "w", encoding="utf-8") as f:
        f.write(example_server)
    
    # 添加执行权限
    os.chmod("example_mcp_server.py", 0o755)
    print("✅ 创建示例MCP服务器: example_mcp_server.py")

def create_start_script():
    """创建启动脚本"""
    start_script = """#!/bin/bash
# MCP网络桥接服务启动脚本

echo "🚀 启动MCP网络桥接服务..."

# 默认配置
SERVER_COMMAND="python3 example_mcp_server.py"
PORT=8080
SERVICE_NAME="示例MCP服务"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--server-command)
            SERVER_COMMAND="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -n|--service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG="--debug"
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo "选项:"
            echo "  -c, --server-command  MCP服务器启动命令 (默认: python3 example_mcp_server.py)"
            echo "  -p, --port           WebSocket端口 (默认: 8080)"
            echo "  -n, --service-name   服务名称 (默认: 示例MCP服务)"
            echo "  -d, --debug          启用调试模式"
            echo "  -h, --help          显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

echo "📋 配置信息:"
echo "  服务器命令: $SERVER_COMMAND"
echo "  端口: $PORT"
echo "  服务名称: $SERVICE_NAME"

# 检查Python和依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到Python3，请先安装Python3"
    exit 1
fi

# 启动桥接服务
python3 mcp_network_bridge.py \\
    --server-command "$SERVER_COMMAND" \\
    --port "$PORT" \\
    --service-name "$SERVICE_NAME" \\
    $DEBUG
"""
    
    with open("start_bridge.sh", "w", encoding="utf-8") as f:
        f.write(start_script)
    
    # 添加执行权限
    os.chmod("start_bridge.sh", 0o755)
    print("✅ 创建启动脚本: start_bridge.sh")

def main():
    print("🔧 MCP网络桥接服务安装程序")
    print("=" * 50)
    
    # 安装依赖
    if not install_dependencies():
        return False
    
    # 创建示例服务器
    create_example_server()
    
    # 创建启动脚本
    create_start_script()
    
    print("\n✅ 安装完成！")
    print("\n📖 使用说明:")
    print("1. 启动示例服务器: ./start_bridge.sh")
    print("2. 使用自定义MCP服务器: ./start_bridge.sh -c \"python3 your_mcp_server.py\"")
    print("3. 指定端口: ./start_bridge.sh -p 9090")
    print("4. 启用调试模式: ./start_bridge.sh -d")
    print("\n📱 在iOS应用中，会自动发现并连接到此服务")
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1) 