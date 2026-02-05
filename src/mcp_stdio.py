"""MCP STDIO bridge for Claude Desktop integration.

This module provides an STDIO transport layer for MCP, allowing Claude Desktop
to spawn DocsMCP as a subprocess and communicate via stdin/stdout.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import handle_mcp_request, MCP_CAPABILITIES
from models import MCPRequest


async def handle_line(line: str) -> str:
    """Process a single JSON-RPC request line."""
    try:
        data = json.loads(line)
        request = MCPRequest(**data)
        response = await handle_mcp_request(request)
        return json.dumps(response.model_dump(exclude_none=True))
    except json.JSONDecodeError as e:
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": f"Parse error: {e}"},
            "id": None,
        })
    except Exception as e:
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": None,
        })


async def main():
    """Main STDIO loop."""
    # Send capabilities on startup
    print(json.dumps({
        "jsonrpc": "2.0",
        "result": {"capabilities": MCP_CAPABILITIES},
        "id": 0,
    }), flush=True)
    
    # Read from stdin, write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            
            line = line.decode().strip()
            if not line:
                continue
            
            response = await handle_line(line)
            print(response, flush=True)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": None,
            }), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
