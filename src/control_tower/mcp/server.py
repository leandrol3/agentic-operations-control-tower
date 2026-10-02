"""Official MCP SDK over stdio; same image, transient role, no extra port/service."""
from mcp.server.fastmcp import FastMCP
from .tools import register_tools
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError
from ..application import ApplicationError


class PublicMCPServer(FastMCP):
    """Redact SDK validation errors: invalid caller payloads are not public output."""
    async def call_tool(self, name, arguments):
        try:
            return await super().call_tool(name, arguments)
        except Exception as error:
            cause = error
            while cause.__cause__ is not None:
                cause = cause.__cause__
            if isinstance(cause, ApplicationError):
                raise ToolError(f'{cause.code}: {cause.detail}') from None
            if isinstance(cause, ValidationError):
                raise ToolError('422: Request inválido; consulte o schema da tool') from None
            raise ToolError('Tool indisponível; confira nome e configuração do runtime') from None


def create_server(capability):
    server = PublicMCPServer('NovaCore Incident Capability')
    register_tools(server, capability)
    return server


def main():
    from ..application import IncidentCapability
    from ..runtime.settings import RuntimeSettings
    from ..runtime.bootstrap import configure
    from ..runtime.store import CorrelatedStore
    from ..telemetry import tracing
    settings = RuntimeSettings()
    configure(settings)
    # stdout belongs exclusively to the MCP JSON-RPC transport.
    import sys
    from ..telemetry.logging import LOGGER
    for handler in LOGGER.handlers:
        handler.setStream(sys.stderr)
    if settings.llm_mode == 'openai':
        from ..settings import Settings
        Settings.load(settings.control_tower_root)
    from ..distributed.producer import enqueue
    store = CorrelatedStore(settings.database_url.get_secret_value())
    store.initialize()
    tracing.initialize_tracing(settings)
    try:
        create_server(IncidentCapability(settings, store, enqueue)).run(transport='stdio')
    finally:
        tracing.shutdown()


if __name__ == '__main__':
    main()
