#!/usr/bin/env python3
"""
MCP统一网关服务器
管理多个MCP服务器，提供统一的WebSocket接口给iOS客户端
"""

import asyncio
import websockets
import json
import subprocess
import sys
import argparse
import logging
import signal
import os
from typing import Optional, Dict, Any, List
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServerManager:
    """MCP服务器管理器"""
    
    def __init__(self, server_id: str, config: Dict[str, Any]):
        self.server_id = server_id
        self.config = config
        self.prefix = config.get("prefix", server_id)
        self.process: Optional[subprocess.Popen] = None
        self.name = config.get("name", server_id)
        
    async def start(self):
        """启动MCP服务器进程"""
        try:
            logger.info(f"🚀 启动MCP服务器: {self.name} ({self.server_id})")
            
            env = os.environ.copy()
            env.update(self.config.get("env", {}))
            
            self.process = subprocess.Popen(
                self.config["command"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            
            logger.info(f"✅ MCP服务器启动成功: {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动MCP服务器失败 {self.name}: {e}")
            return False
    
    async def send_message(self, message: str) -> str:
        """发送消息到MCP服务器并返回响应"""
        if not self.process or self.process.poll() is not None:
            raise Exception(f"MCP服务器 {self.name} 未运行")
        
        try:
            self.process.stdin.write(message + "\n")
            self.process.stdin.flush()
            
            response = self.process.stdout.readline()
            return response.strip() if response else ""
            
        except Exception as e:
            logger.error(f"❌ MCP服务器通信错误 {self.name}: {e}")
            raise
    
    def stop(self):
        """停止MCP服务器"""
        if self.process and self.process.poll() is None:
            logger.info(f"🛑 停止MCP服务器: {self.name}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

class MCPGateway:
    """MCP统一网关"""
    
    def __init__(self, config_path: str = "mcp_servers.json"):
        self.config_path = config_path
        self.config = {}
        self.servers: Dict[str, MCPServerManager] = {}
        self.clients = {}  # websocket -> client_id 映射
        self.client_counter = 0
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"✅ 配置文件加载成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            return False
    
    async def start_all_servers(self):
        """启动所有MCP服务器"""
        if not self.config:
            return False
        
        servers_config = self.config.get("servers", {})
        success_count = 0
        
        for server_id, server_config in servers_config.items():
            manager = MCPServerManager(server_id, server_config)
            if await manager.start():
                self.servers[server_id] = manager
                success_count += 1
            else:
                logger.error(f"❌ 跳过失败的服务器: {server_id}")
        
        logger.info(f"✅ 成功启动 {success_count}/{len(servers_config)} 个MCP服务器")
        return success_count > 0
    
    async def handle_websocket(self, websocket):
        """处理WebSocket客户端连接"""
        self.client_counter += 1
        client_id = f"client_{self.client_counter}"
        client_addr = websocket.remote_address
        
        logger.info(f"🔗 新的iOS客户端连接: {client_addr} (ID: {client_id})")
        self.clients[websocket] = client_id
        
        try:
            async for message in websocket:
                try:
                    logger.info(f"📥 收到来自 {client_id} 的消息")
                    logger.debug(f"📄 消息内容: {message}")
                    
                    response = await self.process_message(message)
                    if response:
                        await websocket.send(response)
                        logger.info(f"📤 发送响应到 {client_id}")
                        
                except Exception as e:
                    logger.error(f"❌ 处理消息时出错 {client_id}: {e}")
                    logger.error(traceback.format_exc())
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 客户端正常断开: {client_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket处理错误 {client_id}: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.clients.pop(websocket, None)
            logger.info(f"🧹 清理客户端连接: {client_id} (剩余: {len(self.clients)})")
    
    async def process_message(self, message: str) -> str:
        """处理MCP消息"""
        try:
            msg_data = json.loads(message)
            method = msg_data.get("method", "")
            
            if method == "initialize":
                return await self.handle_initialize(msg_data)
            elif method == "tools/list":
                return await self.handle_tools_list(msg_data)
            elif method == "resources/list":
                return await self.handle_resources_list(msg_data)
            elif method == "tools/call":
                return await self.handle_tool_call(msg_data)
            elif method == "notifications/initialized":
                return json.dumps({"jsonrpc": "2.0"})
            else:
                # 转发到第一个可用的服务器
                if self.servers:
                    first_server = next(iter(self.servers.values()))
                    return await first_server.send_message(message)
                
        except Exception as e:
            logger.error(f"❌ 消息处理错误: {e}")
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_data.get("id"),
                "error": {"code": -1, "message": str(e)}
            })
    
    async def handle_initialize(self, msg_data: Dict[str, Any]) -> str:
        """处理初始化请求"""
        gateway_config = self.config.get("gateway", {})
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_data.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": gateway_config.get("name", "MCP统一网关"),
                    "version": gateway_config.get("version", "1.0.0")
                }
            }
        }
        
        logger.info("🔄 MCP协议初始化成功")
        return json.dumps(response)
    
    async def handle_tools_list(self, msg_data: Dict[str, Any]) -> str:
        """处理工具列表请求 - 聚合所有服务器的工具"""
        all_tools = []
        
        for server_id, server in self.servers.items():
            try:
                # 向每个服务器请求工具列表
                tools_request = json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                })
                
                response_str = await server.send_message(tools_request)
                if response_str:
                    response_data = json.loads(response_str)
                    tools = response_data.get("result", {}).get("tools", [])
                    
                    # 为工具添加前缀
                    for tool in tools:
                        tool["name"] = f"{server.prefix}:{tool['name']}"
                        tool["description"] = f"[{server.name}] {tool.get('description', '')}"
                    
                    all_tools.extend(tools)
                    logger.info(f"✅ 从 {server.name} 获取到 {len(tools)} 个工具")
                    
            except Exception as e:
                logger.error(f"❌ 获取 {server.name} 工具列表失败: {e}")
        
        response = {
            "jsonrpc": "2.0", 
            "id": msg_data.get("id"),
            "result": {"tools": all_tools}
        }
        
        logger.info("=" * 80)
        logger.info(f"🔧 MCP网关聚合工具列表 (总计 {len(all_tools)} 个):")
        logger.info("=" * 80)
        for i, tool in enumerate(all_tools, 1):
            logger.info(f"{i:2d}. 🛠️  {tool.get('name', 'Unknown')}")
            logger.info(f"     📝 {tool.get('description', 'No description')}")
        logger.info("=" * 80)
        
        return json.dumps(response)
    
    async def handle_resources_list(self, msg_data: Dict[str, Any]) -> str:
        """处理资源列表请求"""
        response = {
            "jsonrpc": "2.0",
            "id": msg_data.get("id"), 
            "result": {"resources": []}
        }
        return json.dumps(response)
    
    async def handle_tool_call(self, msg_data: Dict[str, Any]) -> str:
        """处理工具调用请求 - 根据前缀路由到对应服务器"""
        try:
            params = msg_data.get("params", {})
            tool_name = params.get("name", "")
            
            # 解析工具前缀
            if ":" in tool_name:
                prefix, actual_tool_name = tool_name.split(":", 1)
                
                # 找到对应的服务器
                target_server = None
                for server in self.servers.values():
                    if server.prefix == prefix:
                        target_server = server
                        break
                
                if target_server:
                    # 修改工具名称并转发
                    modified_params = params.copy()
                    modified_params["name"] = actual_tool_name
                    
                    modified_msg = msg_data.copy()
                    modified_msg["params"] = modified_params
                    
                    logger.info(f"🎯 路由工具调用 {tool_name} 到服务器 {target_server.name}")
                    return await target_server.send_message(json.dumps(modified_msg))
                else:
                    logger.error(f"❌ 未找到前缀 {prefix} 对应的服务器")
            else:
                logger.error(f"❌ 工具名称缺少前缀: {tool_name}")
            
            # 返回错误响应
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_data.get("id"),
                "error": {"code": -1, "message": f"工具 {tool_name} 不存在"}
            })
            
        except Exception as e:
            logger.error(f"❌ 工具调用处理错误: {e}")
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_data.get("id"),
                "error": {"code": -1, "message": str(e)}
            })
    
    async def start_server(self):
        """启动网关服务器"""
        if not self.load_config():
            return False
        
        if not await self.start_all_servers():
            logger.error("❌ 没有可用的MCP服务器")
            return False
        
        gateway_config = self.config.get("gateway", {})
        host = gateway_config.get("host", "0.0.0.0")
        port = gateway_config.get("port", 8765)
        
        logger.info(f"🚀 启动MCP统一网关服务器...")
        logger.info(f"📡 监听地址: {host}:{port}")
        logger.info(f"🔧 管理的MCP服务器: {len(self.servers)} 个")
        
        try:
            async with websockets.serve(
                self.handle_websocket,
                host,
                port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            ):
                logger.info("=" * 60)
                logger.info("✅ MCP统一网关启动成功!")
                logger.info("=" * 60)
                logger.info(f"📱 iOS模拟器连接地址: ws://127.0.0.1:{port}")
                logger.info(f"📱 iOS真机连接地址: ws://[本机IP]:{port}")
                logger.info("🔧 管理的服务器:")
                for server_id, server in self.servers.items():
                    logger.info(f"   - {server.name} (前缀: {server.prefix})")
                logger.info("=" * 60)
                logger.info("🛑 按 Ctrl+C 停止服务")
                logger.info("=" * 60)
                
                await asyncio.Future()
                
        except Exception as e:
            logger.error(f"❌ 启动网关服务器失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def stop(self):
        """停止网关服务"""
        logger.info("🛑 停止MCP统一网关")
        for server in self.servers.values():
            server.stop()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"🛑 收到信号 {signum}")
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP统一网关服务器")
    parser.add_argument("--config", default="mcp_servers.json",
                       help="配置文件路径 (默认: mcp_servers.json)")
    parser.add_argument("--debug", action="store_true",
                       help="启用调试日志")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 调试模式已启用")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建网关服务
    gateway = MCPGateway(args.config)
    
    try:
        asyncio.run(gateway.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 网关启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        gateway.stop()
        logger.info("👋 MCP统一网关已停止")

if __name__ == "__main__":
    main() 