"""MCP Server - REFERENCE SOLUTION"""
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from src.services.credit_score_service import get_credit_score
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_config = load_yaml_config("config/mcp_config.yaml")
_server_name = _config.get("server", {}).get("name", "loan-underwriting-mcp")

mcp_app = FastMCP(_server_name)


@mcp_app.tool()
def get_credit_score_tool(customer_id: str) -> Dict[str, Any]:
    """Look up a customer's credit bureau record by customer_id."""
    return get_credit_score(customer_id)


if __name__ == "__main__":
    mcp_app.run(transport=_config.get("server", {}).get("transport", "stdio"))
