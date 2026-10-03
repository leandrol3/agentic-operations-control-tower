export type Source = "didactic" | "durable";
export type Evidence = {
  metric: string;
  observed: string | null;
  target: string | null;
  unit: string;
  scope: string;
  source: string;
  note: string;
  execution_ids: string[];
};
export type Goal = {
  goal_id: string;
  target: string;
  actual: string | null;
  gap: string | null;
  status: string;
  measurement_window: string;
  evidence_source: string;
  evidence: Evidence;
};
export type Recommendation = {
  recommendation_id: string;
  agent_id: string;
  action: string;
  priority: string;
  reason_pt?: string;
  reason: string;
  evidence: Evidence[];
  current_lifecycle_state: string;
  suggested_lifecycle_state: string | null;
  requires_human_approval: boolean;
};
export type Agent = {
  name_pt: string;
  registry: {
    agent_id: string;
    name: string;
    role: string;
    business_owner: string;
    technical_owner: string;
    version: string;
    status: string;
    lifecycle_state: string;
    execution_type: string;
    model: string | null;
    tools: string[];
    interfaces: string[];
    criticality: string;
    business_goals: { name: string; description: string }[];
  };
  goals: Goal[];
  quality: Evidence;
  economics: Evidence;
  latency: Evidence;
  slos: {
    slo_id: string;
    status: string;
    observed: string | null;
    target: string;
    operator: string;
    severity: string;
  }[];
  cost_trend: string;
  goal_trend: string;
  recommendation: Recommendation | null;
  business_value: {
    value_metric: string;
    value_amount: string | null;
    currency_or_unit: string;
    note: string;
  }[];
  sample_count: number;
};
export type Fact = { id: string; text: string; source: string };
export type Knowledge = {
  id: string;
  type: string;
  title: string;
  summary: string;
  content: string;
  tags: string[];
  source_execution: string;
  source_incident: string;
  source: Source;
  evidence: Fact[];
  related: string[];
  validation_status: string;
  created_at: string;
  updated_at: string;
  generated_by: string;
  provenance: string;
  reviewer: string | null;
  review_note: string | null;
};
export type Plan = {
  plan_id: string;
  agent_id: string;
  diagnosis: string;
  objective: string;
  steps: string[];
  staff_assignments: { name: string; status: string }[];
  evidence: Fact[];
  knowledge_ids: string[];
  expected_result: string;
  risk: string;
  requires_human_approval: boolean;
  status: string;
  generated_by: string;
};
export type Operation = {
  incident_id: string;
  execution_id: string;
  status: string;
  outcome: string | null;
  approval_status: string | null;
  duration_ms: number | null;
  created_at: string;
  completed_at: string | null;
  source: Source;
};
export type Detail = {
  started_at: string | null;
  completed_at: string | null;
  worker_id: string | null;
  execution_id: string;
  incident_id: string;
  status: string;
  outcome: string;
  source: Source;
  duration_ms: number | null;
  trace_id: string | null;
  quality: {
    outcome_type: string;
    fallback_used: boolean | null;
    human_review_required: boolean | null;
    confidence: number | null;
    evidence_complete: boolean | null;
    policy_compliant: boolean | null;
  };
  economics: {
    llm_calls: number | null;
    input_tokens: number | null;
    output_tokens: number | null;
    retry_count: number;
    fallback_used: boolean | null;
    estimated_llm_cost: string | null;
    cost_source: string;
    pricing_version: string | null;
    reference_date: string | null;
  };
  result: {
    action: string | null;
    approval: string | null;
    actions_executed: boolean;
  };
  events: { id: number; agent: string; type: string; timestamp: string }[];
};
export type Snapshot = {
  runtime_mode: string;
  source: Source;
  updated_at: string;
  agents: Agent[];
  overview: {
    total_agents: number;
    active_agents: number;
    attention_agents: number;
    goals: Record<string, number>;
    slo_violations: number;
    degraded_executions: number;
    estimated_cost_usd: string | null;
    cost_window: string;
    cost_sample_count: number;
    realized_business_value: null;
    pending_recommendations: number;
    alerts: number;
  };
  alerts: {
    id: string;
    agent_id: string;
    severity: string;
    message: string;
    source: string;
    timestamp: string;
    recommendation: string | null;
  }[];
  recommendations: Recommendation[];
  operations: Operation[];
  knowledge: {
    items: Knowledge[];
    counts: Record<string, number>;
    types: Record<string, number>;
    links: { from: string; to: string; label: string }[];
  };
  plans: Plan[];
  chart: { agent: string; target: number; actual: number | null }[];
  settings: {
    decision_rules: string[];
    thresholds: {
      version: string;
      window_size: number;
      min_samples: number;
      slos: {
        slo_id: string;
        target: string;
        operator: string;
        severity: string;
      }[];
    };
    pricing: {
      version: string;
      reference_date: string;
      models: Record<
        string,
        {
          input_per_million: string;
          cached_input_per_million: string;
          output_per_million: string;
          currency: string;
        }
      >;
    };
    demo_profile: string;
    lifecycle_edges: { from: string; to: string }[];
  };
};
