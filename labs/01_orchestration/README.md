# Aula 1 — Architecture & Orchestration
1. Teoria: coordenação como problema de engenharia; leia docs/case/NOVACORE.md.
2. Problema: Alpha atrasa M42; quais pedidos, estoques e clientes se conectam?
3. Demonstração: execute os comandos incident e tools do README.
4. Codificação conjunta (TODOs): desenhe estado e contratos de investigação; implemente especialistas;
   Supervisor seleciona especialistas; LangGraph paraleliza Supply/Production/Logistics e reúne evidências;
   Finance compara cenários; Challenger testa premissas; produza Recommendation com aprovação humana.
5. Experimento inicial: compare get_stock("M42", "Campinas") e get_stock("M42", "São Paulo").
   Calcule multas para 0, 1 e 7 dias. Explique por que prazo de fornecedor não equivale a atraso do cliente.
6. Reflexão: onde está o estado? Quem decide? Qual parte deveria ser código determinístico?

O start termina na exploração das capabilities. TODOs não são testes quebrados nem solução oculta.
Critério futuro de complete: INCIDENT-001 percorre o grafo, resultados validados, challenger e aprovação,
mock com os mesmos contratos do provider real, testes de routing, estado e saída inválida.
