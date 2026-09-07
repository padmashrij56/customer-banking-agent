"""
MCP Server - exposes ONE enterprise capability (credit bureau lookup) as a
Model Context Protocol tool (Scope Decision 2: one clean example of the
protocol, not a full tool-surface migration).

TODO: Participants will implement the get_credit_score_tool() body
(Activity 2.1). The FastMCP server instance and tool registration
(everything else in this file) are prefilled plumbing.
"""
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from src.services.credit_score_service import get_credit_score
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_config = load_yaml_config("config/mcp_config.yaml")
_server_name = _config.get("server", {}).get("name", "loan-underwriting-mcp")

# Prefilled: the FastMCP server instance. Registering a tool with
# @mcp_app.tool() below only records its name/signature/docstring - it does
# NOT call the function, so this module can be imported safely even before
# the tool body is implemented.
mcp_app = FastMCP(_server_name)


@mcp_app.tool()
def get_credit_score_tool(customer_id: str) -> Dict[str, Any]:
    """
    Look up a customer's credit bureau record by customer_id.

    TODO (Activity 2.1): Delegate to
    src.services.credit_score_service.get_credit_score(customer_id) and
    return its result directly - FastMCP serializes the returned dict as the
    tool's JSON result. This is the one enterprise capability this MCP
    server wraps (config/mcp_config.yaml's tools.get_credit_score entry
    documents its declared shape).
    """
    # TODO: call get_credit_score(customer_id) and return its result.
    return get_credit_score(customer_id)
    raise NotImplementedError("get_credit_score_tool is not implemented yet - see src/mcp/mcp_server.py")


if __name__ == "__main__":
    # Runs this server over the transport declared in
    # config/mcp_config.yaml's server.transport (stdio - src/mcp/mcp_client.py
    # launches this module as a subprocess and speaks MCP to it over
    # stdin/stdout). No network call is involved (Scope Decision 2 keeps
    # this to a local, single-tool example).
    mcp_app.run(transport=_config.get("server", {}).get("transport", "stdio"))
