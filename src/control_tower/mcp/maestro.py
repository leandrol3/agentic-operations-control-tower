"""Optional MCP boundary for the same Maestro used by the cockpit HTTP API."""

from ..cockpit.conversation import Conversations
from ..cockpit.models import MaestroRequest, MaestroResponse
from ..telemetry import tracing


def register_maestro(server, service_factory):
    # Session history is local to this MCP process; persisted plans/knowledge are shared.
    conversations = Conversations()

    @server.tool()
    def ask_maestro(request: MaestroRequest) -> MaestroResponse:
        """Consult workforce evidence and approved knowledge; persist a proposed plan.

        Reuse returned session_id for follow-ups in this MCP connection. Source didactic
        is synthetic; durable reads operational history. This tool never approves
        knowledge, executes a plan, changes lifecycle, or authorizes business actions.
        """
        with tracing.operation('mcp tool ask_maestro'):
            return MaestroResponse.model_validate(
                conversations.chat(service_factory(), request)
            )
