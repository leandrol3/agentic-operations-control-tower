"""Three public tools; all execution stays behind the shared capability/queue."""
from uuid import UUID
from ..api.models import (IncidentSubmissionRequest, ExecutionAcceptedResponse,
                          ExecutionStatusResponse, ExecutionResultResponse)
from ..telemetry import tracing


def register_tools(server, capability):
    def invoke(name, operation, *args):
        # SDK generates real spans when enabled. No invented remote parent context.
        with tracing.operation('mcp tool ' + name):
            return operation(*args)

    @server.tool()
    def submit_incident(request: IncidentSubmissionRequest) -> ExecutionAcceptedResponse:
        """Submit the reference investigation to the queue; does not execute actions."""
        return invoke('submit_incident', capability.submit_incident, request)

    @server.tool()
    def get_execution_status(execution_id: UUID) -> ExecutionStatusResponse:
        """Read public runtime status for an accepted execution."""
        return invoke('get_execution_status', capability.execution_status, execution_id)

    @server.tool()
    def get_execution_result(execution_id: UUID) -> ExecutionResultResponse:
        """Read the public result; pending execution has no outcome yet."""
        return invoke('get_execution_result', capability.result, execution_id)
