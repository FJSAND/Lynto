#!/usr/bin/env python3
"""
高德地图MCP桥接服务器
将stdio模式的@amap/amap-maps-mcp-server桥接到WebSocket，供iOS客户端连接
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
from typing import Optional, Dict, Any
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmapMCPBridge:
    """高德地图MCP桥接服务器"""
    
    def __init__(self, port: int = 8766, api_key: str = "1ebda571f9bdf2ae81cf71d1cb66ce57"):
        self.port = port
        self.api_key = api_key
        self.amap_process: Optional[subprocess.Popen] = None
        self.clients = {}  # websocket -> client_id 映射
        self.client_counter = 0
        
    async def start_amap_server(self):
        """启动高德地图MCP服务器进程"""
        logger.info("🗺️ 启动高德地图MCP服务器...")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env["AMAP_MAPS_API_KEY"] = self.api_key
            
            # 启动高德地图MCP服务器
            self.amap_process = subprocess.Popen(
                ["npx", "-y", "@amap/amap-maps-mcp-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # 无缓冲
                env=env
            )
            
            logger.info("✅ 高德地图MCP服务器进程启动成功")
            logger.info(f"📍 API密钥: {self.api_key[:10]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动高德地图MCP服务器失败: {e}")
            return False
    
    async def handle_websocket(self, websocket):
        """处理WebSocket客户端连接"""
        self.client_counter += 1
        client_id = f"client_{self.client_counter}"
        client_addr = websocket.remote_address
        
        logger.info(f"🔗 新的iOS客户端连接: {client_addr} (ID: {client_id})")
        
        self.clients[websocket] = client_id
        
        try:
            # 为每个客户端启动一个独立的高德MCP服务器实例
            client_process = await self.start_client_amap_server()
            
            if not client_process:
                logger.error(f"❌ 为客户端 {client_id} 启动高德服务器失败")
                return
            
            logger.info(f"✅ 为客户端 {client_id} 启动了独立的高德MCP服务器")
            
            # 创建读取任务
            read_task = asyncio.create_task(
                self.read_from_amap(client_process, websocket, client_id)
            )
            
            try:
                async for message in websocket:
                    try:
                        logger.info(f"📥 收到来自 {client_id} 的消息")
                        logger.debug(f"📄 消息内容: {message}")
                        
                        # 验证JSON格式
                        try:
                            json_msg = json.loads(message)
                            logger.info(f"🔍 MCP方法: {json_msg.get('method', 'unknown')}")
                        except json.JSONDecodeError:
                            logger.error(f"❌ JSON解析失败: {message}")
                            continue
                        
                        # 转发到高德MCP服务器
                        client_process.stdin.write(message + "\n")
                        client_process.stdin.flush()
                        logger.debug(f"📤 转发消息到高德服务器: {client_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ 处理消息时出错 {client_id}: {e}")
                        logger.error(traceback.format_exc())
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"📱 客户端正常断开: {client_id}")
            finally:
                # 清理客户端进程
                read_task.cancel()
                if client_process and client_process.poll() is None:
                    client_process.terminate()
                    try:
                        client_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        client_process.kill()
                logger.info(f"🧹 清理客户端 {client_id} 的高德服务器进程")
                
        except Exception as e:
            logger.error(f"❌ WebSocket处理错误 {client_id}: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.clients.pop(websocket, None)
            logger.info(f"🧹 清理客户端连接: {client_id} (剩余: {len(self.clients)})")
    
    async def start_client_amap_server(self):
        """为单个客户端启动高德MCP服务器实例"""
        try:
            env = os.environ.copy()
            env["AMAP_MAPS_API_KEY"] = self.api_key
            
            process = subprocess.Popen(
                ["npx", "-y", "@amap/amap-maps-mcp-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            
            return process
        except Exception as e:
            logger.error(f"❌ 启动客户端高德服务器失败: {e}")
            return None
    
    async def read_from_amap(self, process, websocket, client_id):
        """从高德MCP服务器读取响应并转发到WebSocket客户端"""
        try:
            while True:
                # 非阻塞读取stdout
                line = await asyncio.get_event_loop().run_in_executor(
                    None, process.stdout.readline
                )
                
                if not line:
                    logger.warning(f"⚠️ 高德服务器输出结束: {client_id}")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # 验证JSON响应
                    response_data = json.loads(line)
                    logger.info(f"📤 转发高德响应到 {client_id}")
                    logger.debug(f"📄 响应内容: {line}")
                    
                    # 如果是工具列表响应，打印详细信息
                    if (response_data.get("result") and 
                        "tools" in response_data.get("result", {})):
                        tools = response_data["result"]["tools"]
                        logger.info("=" * 80)
                        logger.info(f"🔧 高德地图MCP服务器提供的工具列表 ({len(tools)} 个):")
                        logger.info("=" * 80)
                        for i, tool in enumerate(tools, 1):
                            logger.info(f"{i:2d}. 🛠️  {tool.get('name', 'Unknown')}")
                            logger.info(f"     📝 描述: {tool.get('description', 'No description')}")
                            if 'inputSchema' in tool:
                                schema = tool['inputSchema']
                                if 'properties' in schema:
                                    logger.info(f"     📋 参数: {list(schema['properties'].keys())}")
                                if 'required' in schema:
                                    logger.info(f"     ⚠️  必需: {schema['required']}")
                            logger.info("")
                        logger.info("=" * 80)
                    
                    # 如果是资源列表响应，也打印一下
                    elif (response_data.get("result") and 
                          "resources" in response_data.get("result", {})):
                        resources = response_data["result"]["resources"]
                        if resources:
                            logger.info(f"📚 高德地图MCP服务器提供的资源: {len(resources)} 个")
                            for resource in resources:
                                logger.info(f"   - 📄 {resource.get('name', 'Unknown')}: {resource.get('description', 'No description')}")
                        else:
                            logger.info("📚 高德地图MCP服务器未提供资源")
                    
                    # 发送到WebSocket客户端
                    await websocket.send(line)
                    
                except json.JSONDecodeError:
                    logger.debug(f"🔍 非JSON输出 {client_id}: {line}")
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"📱 客户端连接已关闭: {client_id}")
                    break
                except Exception as e:
                    logger.error(f"❌ 转发响应时出错 {client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ 读取高德服务器输出时出错 {client_id}: {e}")
            logger.error(traceback.format_exc())
    
    async def start_server(self):
        """启动WebSocket桥接服务器"""
        logger.info(f"🚀 启动高德地图MCP WebSocket桥接服务器...")
        logger.info(f"📡 监听端口: {self.port}")
        logger.info(f"🗺️ 高德API密钥: {self.api_key[:10]}...")
        
        try:
            async with websockets.serve(
                self.handle_websocket,
                "0.0.0.0",
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            ):
                logger.info("=" * 60)
                logger.info("✅ 高德地图MCP WebSocket桥接服务器启动成功!")
                logger.info("=" * 60)
                logger.info(f"📱 iOS模拟器连接地址: ws://127.0.0.1:{self.port}")
                logger.info(f"📱 iOS真机连接地址: ws://[本机IP]:{self.port}")
                logger.info(f"🗺️ 高德地图API服务: 地理编码、逆地理编码、路径规划等")
                logger.info("=" * 60)
                logger.info("🛑 按 Ctrl+C 停止服务")
                logger.info("=" * 60)
                
                # 保持服务运行
                await asyncio.Future()
                
        except Exception as e:
            logger.error(f"❌ 启动WebSocket服务器失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def stop(self):
        """停止服务"""
        logger.info("🛑 停止高德地图MCP桥接服务")
        
        # 停止主高德服务器进程
        if self.amap_process and self.amap_process.poll() is None:
            logger.info("🗺️ 停止高德地图MCP服务器进程")
            self.amap_process.terminate()
            try:
                self.amap_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.amap_process.kill()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"🛑 收到信号 {signum}")
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="高德地图MCP WebSocket桥接服务器")
    parser.add_argument("--port", type=int, default=8766,
                       help="WebSocket端口 (默认: 8766)")
    parser.add_argument("--api-key", default="1ebda571f9bdf2ae81cf71d1cb66ce57",
                       help="高德地图API密钥")
    parser.add_argument("--debug", action="store_true",
                       help="启用调试日志")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 调试模式已启用")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建桥接服务
    bridge = AmapMCPBridge(args.port, args.api_key)
    
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        bridge.stop()
        logger.info("👋 高德地图MCP桥接服务已停止")

if __name__ == "__main__":
    main() 