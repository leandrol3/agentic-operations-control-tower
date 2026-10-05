"""Two short turns via the actual MCP client; no approval or operational action."""
import asyncio
from pathlib import Path
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from control_tower.cockpit.models import MaestroResponse


async def main():
    launcher = Path(__file__).resolve().with_name('start_maestro_mcp.sh')
    Path('artifacts').mkdir(exist_ok=True)
    with Path('artifacts/maestro-mcp.log').open('a') as logs:
        async with stdio_client(StdioServerParameters(command='/bin/bash', args=[str(launcher)]), errlog=logs) as streams:
            async with ClientSession(*streams) as client:
                await client.initialize()
                names = [t.name for t in (await client.list_tools()).tools]
                assert 'ask_maestro' in names
                print('MCP conectado · ask_maestro disponível', flush=True)
                session_id = None
                for question in ['Como posso melhorar o agente de Supply?', 'Que conhecimento aprovado sustenta essa proposta?']:
                    request = {'question': question, 'agent_id': 'supply', 'source': 'didactic'}
                    if session_id:
                        request['session_id'] = session_id
                    started = time.perf_counter()
                    result = await client.call_tool('ask_maestro', {'request': request})
                    if result.isError:
                        raise SystemExit('Maestro indisponível via MCP; use o fallback preparado. Consulte artifacts/maestro-mcp.log.')
                    response = MaestroResponse.model_validate(result.structuredContent)
                    session_id = response.session_id
                    plan = response.plan
                    print(f'\n{question}\nGerador: {plan.generated_by} · {time.perf_counter()-started:.2f} s')
                    print(plan.diagnosis)
                    print('Objetivo:', plan.objective)
                    print('Conhecimento aprovado:', ', '.join(plan.knowledge_ids) or 'Nenhum disponível')
                    print('Fontes consultadas:', ', '.join(response.sources_consulted))
                    print('Plano:', plan.plan_id, '|', plan.status, '| aprovação humana obrigatória')
                    print('Nenhuma ação operacional ou aprovação de conhecimento executada.', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
