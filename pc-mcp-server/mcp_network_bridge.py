#!/usr/bin/env python3
"""
MCP网络桥接服务器
将本地MCP服务（StdioTransport）桥接为网络服务，供iOS应用连接

使用方法:
    python mcp_network_bridge.py --server-command "python my_mcp_server.py" --port 8080
"""

import asyncio
import json
import logging
import argparse
import subprocess
import signal
import sys
from typing import Optional, Dict, Any
import websockets
import zeroconf
from zeroconf import ServiceInfo
import socket

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCPNetworkBridge')

class MCPNetworkBridge:
    """MCP网络桥接服务器"""
    
    def __init__(self, server_command: str, port: int = 8080, service_name: str = "MCP服务"):
        self.server_command = server_command
        self.port = port
        self.service_name = service_name
        self.process: Optional[subprocess.Popen] = None
        self.zeroconf_service: Optional[zeroconf.Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self.connected_clients: Dict[websockets.WebSocketServerProtocol, str] = {}
        
    async def start_mcp_server(self):
        """启动本地MCP服务器进程"""
        logger.info(f"🚀 启动MCP服务器: {self.server_command}")
        
        try:
            self.process = subprocess.Popen(
                self.server_command.split(),
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
    
    def stop_mcp_server(self):
        """停止MCP服务器进程"""
        if self.process:
            logger.info("🛑 停止MCP服务器进程")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
    
    def register_service(self):
        """注册Bonjour/mDNS服务"""
        logger.info(f"📡 注册网络服务: {self.service_name}")
        
        try:
            # 获取本机IP地址
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # 创建服务信息
            self.zeroconf_service = zeroconf.Zeroconf()
            self.service_info = ServiceInfo(
                "_mcp._tcp.local.",
                f"{self.service_name}._mcp._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={
                    b"version": b"1.0.0",
                    b"protocol": b"mcp-2024-11-05",
                    b"transport": b"websocket",
                    b"description": self.service_name.encode('utf-8')
                }
            )
            
            self.zeroconf_service.register_service(self.service_info)
            logger.info(f"✅ 服务注册成功: {local_ip}:{self.port}")
            
        except Exception as e:
            logger.error(f"❌ 服务注册失败: {e}")
    
    def unregister_service(self):
        """注销网络服务"""
        if self.zeroconf_service and self.service_info:
            logger.info("📡 注销网络服务")
            self.zeroconf_service.unregister_service(self.service_info)
            self.zeroconf_service.close()
    
    async def handle_client(self, websocket, path):
        """处理WebSocket客户端连接"""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"📱 新客户端连接: {client_addr}")
        
        self.connected_clients[websocket] = client_addr
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 客户端断开连接: {client_addr}")
        except Exception as e:
            logger.error(f"❌ 处理客户端消息错误: {e}")
        finally:
            if websocket in self.connected_clients:
                del self.connected_clients[websocket]
    
    async def handle_message(self, websocket, message: str):
        """处理来自客户端的MCP消息"""
        try:
            # 解析JSON消息
            data = json.loads(message)
            logger.debug(f"📥 收到MCP消息: {data.get('method', 'unknown')}")
            
            # 转发给MCP服务器
            if self.process and self.process.stdin:
                self.process.stdin.write(message + '\n')
                self.process.stdin.flush()
                
                # 读取响应
                if self.process.stdout:
                    response = self.process.stdout.readline()
                    if response:
                        logger.debug(f"📤 发送MCP响应: {response[:100]}...")
                        await websocket.send(response.strip())
                    else:
                        # 如果没有响应，发送错误消息
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "error": {
                                "code": -32603,
                                "message": "MCP服务器无响应"
                            }
                        }
                        await websocket.send(json.dumps(error_response))
        
        except json.JSONDecodeError:
            logger.error(f"❌ 无效的JSON消息: {message[:100]}...")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            await websocket.send(json.dumps(error_response))
        
        except Exception as e:
            logger.error(f"❌ 处理消息错误: {e}")
    
    async def start_websocket_server(self):
        """启动WebSocket服务器"""
        logger.info(f"🌐 启动WebSocket服务器，端口: {self.port}")
        
        try:
            server = await websockets.serve(
                self.handle_client,
                "0.0.0.0",
                self.port,
                subprotocols=["mcp"]
            )
            logger.info("✅ WebSocket服务器启动成功")
            return server
        except Exception as e:
            logger.error(f"❌ 启动WebSocket服务器失败: {e}")
            return None
    
    async def run(self):
        """运行桥接服务"""
        logger.info("🚀 启动MCP网络桥接服务")
        
        # 启动MCP服务器
        if not await self.start_mcp_server():
            return False
        
        # 注册网络服务
        self.register_service()
        
        # 启动WebSocket服务器
        server = await self.start_websocket_server()
        if not server:
            self.cleanup()
            return False
        
        try:
            logger.info("✅ MCP网络桥接服务运行中...")
            logger.info(f"📱 iOS应用可以连接到: ws://<your-ip>:{self.port}/mcp")
            
            # 保持服务运行
            await server.wait_closed()
            
        except KeyboardInterrupt:
            logger.info("⏹️ 收到停止信号")
        except Exception as e:
            logger.error(f"❌ 服务运行错误: {e}")
        finally:
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理资源...")
        self.stop_mcp_server()
        self.unregister_service()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info("🛑 收到停止信号，正在退出...")
    sys.exit(0)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP网络桥接服务器")
    parser.add_argument(
        "--server-command",
        required=True,
        help="启动MCP服务器的命令"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="WebSocket服务器端口 (默认: 8080)"
    )
    parser.add_argument(
        "--service-name",
        default="MCP服务",
        help="在网络上发布的服务名称"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并运行桥接服务
    bridge = MCPNetworkBridge(
        server_command=args.server_command,
        port=args.port,
        service_name=args.service_name
    )
    
    success = await bridge.run()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️ 程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1) 