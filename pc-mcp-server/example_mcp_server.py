#!/usr/bin/env python3
"""
示例MCP服务器
提供简单的echo和add工具
"""

import json
import sys

def handle_request(request):
    """处理MCP请求"""
    try:
        if request.get("method") == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "example-server",
                        "version": "1.0.0"
                    }
                }
            }
        elif request.get("method") == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": request.get("id"),
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
        elif request.get("method") == "tools/call":
            tool_name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("arguments", {})
            
            if tool_name == "echo":
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
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
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"计算结果: {args.get('a')} + {args.get('b')} = {result}"
                            }
                        ]
                    }
                }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
    
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }

def main():
    """主函数 - 处理stdin/stdout通信"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
