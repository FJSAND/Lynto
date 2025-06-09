#!/usr/bin/env python3
"""
标准MCP服务器实现 - 修复WebSocket握手问题
严格按照官方MCP协议规范: https://github.com/modelcontextprotocol/python-sdk
支持WebSocket和stdio两种传输方式，优化iOS客户端兼容性
"""

import asyncio
import websockets
import json
import sys
import argparse
import logging
from typing import Optional, Dict, Any, List
import traceback
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServer:
    """标准MCP服务器实现"""
    
    def __init__(self):
        self.tools = {
            "echo": {
                "name": "echo",
                "description": "Echo back the input text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to echo back"
                        }
                    },
                    "required": ["text"]
                }
            },
            "add": {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number", 
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                }
            },
            "time": {
                "name": "time",
                "description": "Get current time",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        self.resources = []
        self.prompts = []
        self.server_info = {
            "name": "official-mcp-server",
            "version": "1.0.0"
        }
        
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            logger.info(f"🔄 处理MCP请求: {method} (id: {request_id})")
            logger.debug(f"📋 参数: {params}")
            
            # 根据方法分发请求
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "initialized":
                return await self._handle_initialized(request_id, params)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id, params)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id, params)
            elif method == "prompts/list":
                return await self._handle_prompts_list(request_id, params)
            elif method == "ping":
                return await self._handle_ping(request_id, params)
            else:
                logger.warning(f"⚠️ 未知方法: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 处理请求时出错: {e}")
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        logger.info("🚀 初始化MCP服务器")
        
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2024-11-05")
        capabilities = params.get("capabilities", {})
        
        logger.info(f"📱 客户端信息: {client_info}")
        logger.info(f"📡 协议版本: {protocol_version}")
        logger.info(f"⚙️ 客户端能力: {capabilities}")
        
        # 返回初始化响应
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "logging": {}
                },
                "serverInfo": self.server_info
            }
        }
        
        logger.info("✅ 发送初始化响应")
        return response
    
    async def _handle_initialized(self, request_id: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理初始化完成通知"""
        logger.info("🎉 MCP服务器初始化完成")
        # initialized是通知，不需要响应
        return None
    
    async def _handle_tools_list(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具列表请求"""
        logger.info("📝 返回工具列表")
        
        tools_list = list(self.tools.values())
        logger.info(f"🔧 可用工具 ({len(tools_list)}): {[tool['name'] for tool in tools_list]}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        }
    
    async def _handle_tools_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"🛠️ 调用工具: {tool_name}, 参数: {arguments}")
        
        if tool_name not in self.tools:
            logger.error(f"❌ 未知工具: {tool_name}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        try:
            # 执行工具
            if tool_name == "echo":
                text = arguments.get("text", "")
                result_text = f"🔊 Echo: {text}"
            elif tool_name == "add":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = a + b
                result_text = f"🧮 计算结果: {a} + {b} = {result}"
            elif tool_name == "time":
                import datetime
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result_text = f"⏰ 当前时间: {current_time}"
            else:
                result_text = f"✅ 工具 {tool_name} 执行完成"
            
            logger.info(f"✅ 工具执行成功: {result_text}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 执行工具 {tool_name} 时出错: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    async def _handle_resources_list(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源列表请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.resources
            }
        }
    
    async def _handle_prompts_list(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理提示列表请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": self.prompts
            }
        }
    
    async def _handle_ping(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理ping请求"""
        logger.info("🏓 处理ping请求")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {}
        }

class MCPWebSocketServer:
    """MCP WebSocket服务器 - 优化握手处理"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.mcp_server = MCPServer()
        self.clients = set()
        
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        
    async def handle_client(self, websocket):
        """处理WebSocket客户端连接 - 改进错误处理"""
        client_addr = websocket.remote_address
        
        # 兼容不同版本的websockets库
        try:
            path = getattr(websocket, 'path', '/')
        except AttributeError:
            path = '/'
            
        logger.info(f"🔗 新客户端连接: {client_addr}")
        logger.info(f"📍 连接路径: {path}")
        
        # 安全地获取子协议信息
        try:
            subprotocol = getattr(websocket, 'subprotocol', None)
            logger.info(f"🌐 WebSocket子协议: {subprotocol}")
        except AttributeError:
            logger.info(f"🌐 WebSocket子协议: 未知")
        
        self.clients.add(websocket)
        
        try:
            # 发送连接确认（可选）
            logger.info(f"✅ 客户端 {client_addr} WebSocket连接建立成功")
            
            async for message in websocket:
                try:
                    logger.info(f"📥 收到来自 {client_addr} 的原始消息")
                    logger.debug(f"📄 消息内容: {message}")
                    
                    # 解析JSON请求
                    try:
                        request = json.loads(message)
                        logger.info(f"✅ JSON解析成功: {request.get('method', 'unknown')}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON解析失败: {e}")
                        logger.error(f"📄 原始消息: {message}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        await websocket.send(json.dumps(error_response))
                        continue
                    
                    # 处理MCP请求
                    response = await self.mcp_server.handle_request(request)
                    
                    # 发送响应（如果有）
                    if response is not None:
                        response_json = json.dumps(response, ensure_ascii=False)
                        await websocket.send(response_json)
                        logger.info(f"📤 发送响应到 {client_addr}: {response.get('result', {}).get('tools', 'N/A')}")
                        logger.debug(f"📄 完整响应: {response_json}")
                    else:
                        logger.info(f"ℹ️ 无需响应的通知消息: {request.get('method')}")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"🔌 连接已关闭: {client_addr}")
                    break
                except Exception as e:
                    logger.error(f"❌ 处理客户端消息时出错: {e}")
                    logger.error(traceback.format_exc())
                    
                    # 发送通用错误响应
                    try:
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": f"Internal error: {str(e)}"
                            }
                        }
                        await websocket.send(json.dumps(error_response))
                    except:
                        logger.error("❌ 无法发送错误响应")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 客户端正常断开连接: {client_addr}")
        except Exception as e:
            logger.error(f"❌ WebSocket连接错误 from {client_addr}: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.clients.discard(websocket)
            logger.info(f"🧹 清理客户端连接: {client_addr} (剩余: {len(self.clients)})")
            
    async def start(self):
        """启动WebSocket服务器 - 改进配置"""
        local_ip = self.get_local_ip()
        
        logger.info(f"🚀 启动MCP WebSocket服务器...")
        logger.info(f"📡 监听地址: 0.0.0.0:{self.port}")
        logger.info(f"🏠 本机IP: {local_ip}")
        
        try:
            # 配置WebSocket服务器，优化握手处理
            async with websockets.serve(
                self.handle_client,
                "0.0.0.0",
                self.port,
                ping_interval=30,      # 30秒ping间隔
                ping_timeout=10,       # 10秒ping超时
                close_timeout=10,      # 10秒关闭超时
                max_size=10**6,        # 1MB消息大小限制
                max_queue=32,          # 32个消息队列
                compression=None,      # 禁用压缩以提高兼容性
                origins=None,          # 允许所有来源
                extensions=None        # 禁用扩展以提高兼容性
            ):
                logger.info("=" * 60)
                logger.info("✅ MCP WebSocket服务器启动成功!")
                logger.info("=" * 60)
                logger.info(f"📱 iOS模拟器连接地址: ws://127.0.0.1:{self.port}")
                logger.info(f"📱 iOS真机连接地址: ws://{local_ip}:{self.port}")
                logger.info(f"🔧 可用工具: echo, add, time")
                logger.info("=" * 60)
                logger.info("🛑 按 Ctrl+C 停止服务")
                logger.info("=" * 60)
                
                # 保持服务运行
                await asyncio.Future()
                
        except Exception as e:
            logger.error(f"❌ 启动WebSocket服务器失败: {e}")
            logger.error(traceback.format_exc())
            raise

class MCPStdioServer:
    """MCP stdio服务器"""
    
    def __init__(self):
        self.mcp_server = MCPServer()
        
    async def start(self):
        """启动stdio服务器"""
        logger.info("启动MCP stdio服务器")
        
        try:
            # 读取stdin输入
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # 解析JSON请求
                    request = json.loads(line)
                    
                    # 处理请求
                    response = await self.mcp_server.handle_request(request)
                    
                    # 发送响应（如果有）
                    if response is not None:
                        response_json = json.dumps(response)
                        print(response_json)
                        sys.stdout.flush()
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
        except Exception as e:
            logger.error(f"stdio服务器错误: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="官方MCP协议服务器 - 优化iOS兼容性")
    parser.add_argument("--mode", choices=["websocket", "stdio"], default="websocket",
                       help="服务器模式 (默认: websocket)")
    parser.add_argument("--port", type=int, default=8765,
                       help="WebSocket端口 (默认: 8765)")
    parser.add_argument("--debug", action="store_true",
                       help="启用调试日志")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 调试模式已启用")
    
    try:
        if args.mode == "websocket":
            server = MCPWebSocketServer(args.port)
            asyncio.run(server.start())
        else:
            logger.info("📝 启动stdio模式")
            server = MCPStdioServer()
            asyncio.run(server.start())
            
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 