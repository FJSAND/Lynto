#!/usr/bin/env python3
"""
简化的MCP网络桥接服务器
支持WebSocket连接，兼容iOS NetworkMCPTransport
"""

import asyncio
import websockets
import json
import subprocess
import sys
import argparse
import socket
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPBridge:
    def __init__(self, port: int = 8765, mcp_command: str = "python3 example_mcp_server.py"):
        self.port = port
        self.mcp_command = mcp_command
        self.mcp_process: Optional[subprocess.Popen] = None
        self.clients = set()
        
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    async def start_mcp_server(self):
        """启动MCP服务器进程"""
        logger.info(f"🚀 启动MCP服务器: {self.mcp_command}")
        
        try:
            self.mcp_process = subprocess.Popen(
                self.mcp_command.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            logger.info("✅ MCP服务器进程启动成功")
            return True
        except Exception as e:
            logger.error(f"❌ 启动MCP服务器失败: {e}")
            return False
    
    async def handle_websocket(self, websocket, path):
        """处理WebSocket连接"""
        client_addr = websocket.remote_address
        logger.info(f"📱 新的客户端连接: {client_addr}")
        logger.info(f"🔗 连接路径: {path}")
        
        self.clients.add(websocket)
        
        try:
            # 发送欢迎消息（可选）
            welcome_msg = json.dumps({
                "jsonrpc": "2.0",
                "method": "notification",
                "params": {
                    "message": "WebSocket连接建立成功",
                    "server": "simple-mcp-bridge",
                    "version": "1.0.0"
                }
            })
            await websocket.send(welcome_msg)
            logger.info(f"📤 发送欢迎消息到客户端: {client_addr}")
            
            async for message in websocket:
                logger.info(f"📥 收到来自 {client_addr} 的消息: {message[:200]}...")
                
                # 解析JSON消息
                try:
                    json_msg = json.loads(message)
                    logger.info(f"🔍 解析MCP消息: method={json_msg.get('method', 'unknown')}, id={json_msg.get('id', 'none')}")
                    
                    # 处理MCP消息
                    response = await self.handle_mcp_message(json_msg)
                    if response:
                        response_str = json.dumps(response)
                        await websocket.send(response_str)
                        logger.info(f"📤 发送响应到 {client_addr}: {response_str[:200]}...")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ JSON解析错误 from {client_addr}: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logger.error(f"❌ 处理消息时出错 from {client_addr}: {e}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 客户端断开连接: {client_addr}")
        except Exception as e:
            logger.error(f"❌ WebSocket处理错误 from {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"🧹 清理客户端连接: {client_addr}")
    
    async def handle_mcp_message(self, message):
        """处理MCP协议消息"""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        logger.info(f"🎯 处理MCP方法: {method}")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "simple-mcp-bridge",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "echo",
                                "description": "回显输入的文本",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string", "description": "要回显的文本"}
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
                                        "a": {"type": "number", "description": "第一个数字"},
                                        "b": {"type": "number", "description": "第二个数字"}
                                    },
                                    "required": ["a", "b"]
                                }
                            }
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                if tool_name == "echo":
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Echo: {args.get('text', '')}"
                                }
                            ]
                        }
                    }
                elif tool_name == "add":
                    result = args.get("a", 0) + args.get("b", 0)
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"计算结果: {args.get('a')} + {args.get('b')} = {result}"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
            
            else:
                logger.warning(f"⚠️ 未知的MCP方法: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 处理MCP消息时出错: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def start_server(self):
        """启动WebSocket服务器"""
        local_ip = self.get_local_ip()
        
        logger.info(f"🌐 启动WebSocket服务器...")
        logger.info(f"📡 监听地址: 0.0.0.0:{self.port}")
        logger.info(f"🏠 本机IP: {local_ip}")
        logger.info(f"💻 模拟器连接: ws://127.0.0.1:{self.port}")
        logger.info(f"📱 真机连接: ws://{local_ip}:{self.port}")
        
        try:
            async with websockets.serve(
                self.handle_websocket, 
                "0.0.0.0", 
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            ):
                logger.info("✅ MCP WebSocket服务启动成功!")
                logger.info("🛑 按 Ctrl+C 停止服务")
                
                # 保持服务运行
                await asyncio.Future()  # 永远等待
                
        except Exception as e:
            logger.error(f"❌ 启动WebSocket服务器失败: {e}")
            return False
    
    def stop(self):
        """停止服务"""
        # 停止MCP服务器
        if self.mcp_process:
            logger.info("🛑 停止MCP服务器进程")
            self.mcp_process.terminate()
            self.mcp_process.wait()

def main():
    parser = argparse.ArgumentParser(description="简化的MCP WebSocket桥接服务")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket端口 (默认: 8765)")
    
    args = parser.parse_args()
    
    # 启动桥接服务
    bridge = SimpleMCPBridge(args.port)
    
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    finally:
        bridge.stop()
        logger.info("👋 MCP WebSocket桥接服务已停止")

if __name__ == "__main__":
    main() 