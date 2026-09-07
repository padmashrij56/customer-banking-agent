"""MCP Client - REFERENCE SOLUTION"""
import asyncio
import json
import sys
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_config = load_yaml_config("config/mcp_config.yaml")
_server_module = _config.get("server", {}).get("module", "src.mcp.mcp_server")

_server_params = StdioServerParameters(command=sys.executable, args=["-m", _server_module])


async def _call_get_credit_score(customer_id: str) -> Dict[str, Any]:
    async with stdio_client(_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_credit_score_tool", {"customer_id": customer_id})
            return json.loads(result.content[0].text)


def fetch_credit_score_via_mcp(customer_id: str) -> Dict[str, Any]:
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _call_get_credit_score(customer_id))
        return future.result()
