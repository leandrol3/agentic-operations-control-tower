export const labels: Record<string, string> = {
  mock_no_usage: "Modo mock: sem consumo de tokens",
  usage_unavailable: "Consumo indisponível",
  pricing_unconfigured: "Pricing não configurado",
  configured_pricing_estimate: "Estimativa calculada com pricing configurado",
  active: "Ativo",
  draft: "Rascunho",
  pilot: "Piloto",
  review: "Em revisão",
  paused: "Pausado",
  retired: "Aposentado",
  registered: "Cadastrado",
  on_target: "Dentro da meta",
  at_risk: "Em risco",
  off_target: "Fora da meta",
  unknown: "Desconhecido",
  scale: "Escalar",
  optimize: "Otimizar",
  intervene: "Intervir",
  pause: "Pausar",
  retire: "Aposentar",
  pass: "Dentro do limite",
  warn: "Atenção",
  violation: "Violação",
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  critical: "Crítica",
  stable: "Estável",
  improving: "Melhorando",
  degrading: "Degradando",
  completed: "Concluída",
  running: "Em execução",
  queued: "Na fila",
  failed: "Falhou",
  pending: "Pendente",
  approved: "Aprovado",
  pending_review: "Aguardando revisão",
  rejected: "Rejeitado",
  superseded: "Substituído",
  recommendation: "Recomendação",
  degraded_recommendation: "Recomendação degradada",
  human_review_required: "Revisão humana necessária",
  entity: "Entidade",
  lesson: "Aprendizado",
  pattern: "Padrão",
  decision: "Decisão",
  proposed: "Proposto",
  deterministic: "Determinístico",
  llm_with_deterministic_tools: "LLM + ferramentas determinísticas",
  agent_stage: "Etapa do agente",
  workflow: "Workflow",
  didactic_fixture: "Didático",
  durable_history: "Histórico persistido",
  didactic: "Didático",
  durable: "Histórico persistido",
  completion_rate: "Conclusão / cobertura da etapa",
  stage_latency_p95_ms: "Latência p95 da etapa",
  stage_llm_cost_usd: "Custo LLM atribuído ao papel",
  workflow_degraded_rate: "Resultados degradados no workflow",
  recorded_proposal: "Proposta registrada",
  recommended_scenario_cost: "Custo do cenário proposto",
  workflow_time_to_proposal_ms: "Tempo de runtime até a proposta",
  realized_business_value: "Valor de negócio realizado",
};
export const names: Record<string, string> = {
  supervisor: "Supervisor",
  supply: "Suprimentos",
  production: "Produção",
  logistics: "Logística",
  finance: "Finanças",
  challenger: "Riscos e contestação",
  recommendation: "Recomendação",
  consolidation: "Consolidação",
  human_approval: "Aprovação humana",
  producer: "Produtor",
  worker: "Worker",
};
export const owners: Record<string, string> = {
  Operations: "Operações",
  "Supply Chain": "Cadeia de suprimentos",
  "Production Planning": "Planejamento de produção",
  Logistics: "Logística",
  Finance: "Finanças",
  "Operations Risk": "Riscos operacionais",
  "AI Engineering (didactic ownership)":
    "Engenharia de IA · responsabilidade didática",
};
export const roles: Record<string, string> = {
  supervisor: "Coordenar a investigação operacional.",
  supply: "Reunir evidências de estoque e fornecedores.",
  production: "Analisar ordens e demanda de materiais.",
  logistics: "Avaliar rotas de transporte.",
  finance: "Calcular deterministicamente os custos dos cenários.",
  challenger: "Contestar premissas e validar cenários.",
  recommendation: "Produzir uma proposta estruturada para revisão humana.",
};
export const label = (key: string | null | undefined) =>
  key ? labels[key] || key : "Não disponível";
export function num(value: string | number | null | undefined, unit = "") {
  return value == null
    ? "Não disponível"
    : new Intl.NumberFormat("pt-BR", {
        maximumFractionDigits: unit === "USD" ? 6 : 2,
      }).format(Number(value)) + (unit ? " " + unit : "");
}
export const date = (v: string | null) =>
  v
    ? new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(v))
    : "Não disponível";
