"use client";
import { MaestroPanel, useConversation, type MaestroContext } from "./maestro";
import { LifecycleGraph } from "./lifecycle-graph";
import { useEffect, useState, useRef, type ReactNode } from "react";
import {
  Activity,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleDot,
  Clock3,
  Database,
  FileText,
  GitBranch,
  LayoutDashboard,
  Loader2,
  MessageSquare,
  Network,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
  Wallet,
  X,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Button, Empty } from "./ui";
import { label, names, roles, owners, num, date } from "@/lib/labels";
import type {
  Snapshot,
  Source,
  Agent,
  Knowledge,
  Recommendation,
  Plan,
  Detail,
} from "@/lib/types";
const nav = [
  ["overview", "Visão Geral", LayoutDashboard],
  ["agents", "Agentes", Users],
  ["goals", "Metas", Target],
  ["operations", "Operações", Activity],
  ["quality", "Qualidade", ShieldCheck],
  ["economics", "Economia & Valor", Wallet],
  ["decisions", "Decisões", GitBranch],
  ["alerts", "Alertas", Bell],
  ["lifecycle", "Lifecycle", Network],
  ["maestro", "Maestro", Sparkles],
  ["knowledge", "Segundo Cérebro", BrainCircuit],
  ["loop", "Learning Loop", RefreshCw],
  ["settings", "Configurações", Settings2],
  ["reports", "Relatórios", FileText],
] as const;
async function api<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch("/api/" + path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(data.detail || "Não foi possível concluir a operação.");
  return data;
}
const money = (v: string | null | undefined) =>
  v == null
    ? "Não disponível"
    : new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
        maximumFractionDigits: 0,
      }).format(Number(v));
function Badge({ value, children }: { value?: string; children?: ReactNode }) {
  return (
    <span className={"badge " + (value || "neutral")}>
      {children || label(value)}
    </span>
  );
}
function Panel({
  title,
  tag,
  children,
  className = "",
}: {
  title?: string;
  tag?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={"panel " + className}>
      {title && (
        <div className="panel-title">
          <h3>{title}</h3>
          {tag && <span className="eyebrow">{tag}</span>}
        </div>
      )}
      {children}
    </section>
  );
}
function Facts({
  facts,
}: {
  facts: { id: string; text: string; source: string }[];
}) {
  return (
    <div className="facts">
      {facts.map((f) => (
        <div key={f.id}>
          <Database size={14} />
          <div>
            <b>{f.text}</b>
            <small>
              {label(f.source)} · {f.id}
            </small>
          </div>
        </div>
      ))}
    </div>
  );
}
function Decision({ r }: { r: Recommendation }) {
  return (
    <>
      <div className="inline gap">
        <Badge value={r.action} />
        <Badge value={r.priority} />
      </div>
      <h3 className="decision-title">
        {r.reason_pt || "Revisar as evidências antes de qualquer alteração."}
      </h3>
      <div className="transition">
        <span>{label(r.current_lifecycle_state)}</span>
        <ArrowRight size={16} />
        <span>
          {r.suggested_lifecycle_state
            ? label(r.suggested_lifecycle_state) + " · sugerido"
            : "Sem transição sugerida"}
        </span>
      </div>
      <p className="notice">
        <ShieldCheck size={16} /> Recomendação não é autorização. Aprovação
        humana obrigatória.
      </p>
      <h4>Evidências da recomendação</h4>
      <div className="evidence-grid">
        {r.evidence.map((e, i) => (
          <div key={i}>
            <small>{label(e.metric)}</small>
            <strong>
              {num(e.observed, e.unit === "percent" ? "%" : e.unit)}
            </strong>
            <span>
              Referência: {num(e.target)} · {label(e.scope)}
            </span>
          </div>
        ))}
      </div>
      <Button
        disabled
        title="Disponível somente com Action Authority adequada."
      >
        Executar recomendação · indisponível
      </Button>
    </>
  );
}
function KnowledgeGraph({
  data,
  onOpen,
}: {
  data: Snapshot["knowledge"];
  onOpen: (id: string) => void;
}) {
  const nodes = data.items.slice(0, 12);
  return (
    <div className="graph">
      <svg
        viewBox="0 0 800 330"
        role="img"
        aria-label="Grafo de relações entre documentos de conhecimento"
      >
        {data.links.map((e, i) => {
          const a = nodes.findIndex((n) => n.id === e.from),
            b = nodes.findIndex((n) => n.id === e.to);
          if (a < 0 || b < 0) return null;
          return (
            <line
              key={i}
              x1={130 + (a % 3) * 270}
              y1={55 + Math.floor(a / 3) * 82}
              x2={130 + (b % 3) * 270}
              y2={55 + Math.floor(b / 3) * 82}
              stroke="var(--edge)"
              strokeWidth="2"
            />
          );
        })}
        {nodes.map((n, i) => (
          <g
            key={n.id}
            transform={`translate(${40 + (i % 3) * 270},${25 + Math.floor(i / 3) * 82})`}
            onClick={() => onOpen(n.id)}
            tabIndex={0}
            role="button"
            aria-label={n.title}
            onKeyDown={(e) => e.key === "Enter" && onOpen(n.id)}
          >
            <rect
              width="185"
              height="58"
              rx="10"
              fill={
                n.validation_status === "approved"
                  ? "var(--positive-soft)"
                  : "var(--warning-soft)"
              }
              stroke="var(--edge)"
            />
            <text x="12" y="23" fontSize="11" fill="var(--muted)">
              {label(n.type)} · {label(n.validation_status)}
            </text>
            <text x="12" y="43" fontSize="12" fill="var(--ink)">
              {n.title.slice(0, 24)}
              {n.title.length > 24 ? "…" : ""}
            </text>
            <title>{n.title}</title>
          </g>
        ))}
      </svg>
      <small>
        Relações derivadas dos links dos documentos. Até 12 itens visíveis;
        nenhum graph database.
      </small>
    </div>
  );
}
function Modal({
  children,
  onClose,
}: {
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => previous?.focus();
  }, []);
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        ref={ref}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Detalhe da recomendação"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
          if (e.key === "Tab") {
            const items = ref.current?.querySelectorAll<HTMLElement>(
              'button:not(:disabled),a[href],input,textarea,[tabindex="0"]',
            );
            if (items?.length) {
              const first = items[0],
                last = items[items.length - 1];
              if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
              } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
              }
            }
          }
        }}
      >
        {children}
      </section>
    </div>
  );
}
export default function Cockpit() {
  const [view, setView] = useState("overview"),
    [source, setSource] = useState<Source>("didactic"),
    [data, setData] = useState<Snapshot | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  const [agentId, setAgentId] = useState("supply"),
    [agentOpen, setAgentOpen] = useState(false),
    [tab, setTab] = useState("Resumo"),
    [decision, setDecision] = useState<Recommendation | null>(null);
  const [execution, setExecution] = useState<Detail | null>(null),
    [knowledgeId, setKnowledgeId] = useState<string | null>(null),
    [query, setQuery] = useState(""),
    [busy, setBusy] = useState(""),
    [toast, setToast] = useState("");
  const [reviewer, setReviewer] = useState(""),
    [reviewNote, setReviewNote] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api<Snapshot>("cockpit/overview?source=" + source)
      .then((d) => {
        if (active) {
          setData(d);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (active) {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [source, revision]);
  const go = (v: string) => {
    setView(v);
    setMaestroOverride(null);
    setAgentOpen(false);
    setExecution(null);
    setKnowledgeId(null);
    setToast("");
    window.history.replaceState(null, "", "#" + v);
  };
  const openAgent = (id: string) => {
    setAgentId(id);
    setView("agents");
    setAgentOpen(true);
    setTab("Resumo");
  };
  const current =
    data?.agents.find((a) => a.registry.agent_id === agentId) ||
    data?.agents[0];
  const item = data?.knowledge.items.find((k) => k.id === knowledgeId);
  const refresh = () => setRevision((v) => v + 1);
  const chat = useConversation(refresh);
  const [maestroOpen, setMaestroOpen] = useState(false);
  const [maestroOverride, setMaestroOverride] = useState<MaestroContext | null>(
    null,
  );
  const plan = [...chat.messages].reverse().find((m) => m.reply)?.reply?.plan;
  useEffect(() => {
    setMaestroOverride(null);
  }, [view, execution?.execution_id, knowledgeId, agentId, source]);
  const context: MaestroContext = maestroOverride || {
    context_type: execution
      ? "execution"
      : decision
        ? "recommendation"
        : knowledgeId
          ? "knowledge"
          : view === "lifecycle"
            ? "lifecycle"
            : view === "economics"
              ? "economics"
              : agentOpen || view === "maestro"
                ? "agent"
                : "workforce",
    source,
    route: view,
    ...(execution ? { execution_id: execution.execution_id } : {}),
    ...(decision
      ? {
          recommendation_id: decision.recommendation_id,
          agent_id: decision.agent_id,
        }
      : {}),
    ...(knowledgeId ? { knowledge_id: knowledgeId } : {}),
    ...(!execution &&
    !knowledgeId &&
    !decision &&
    (agentOpen || ["maestro", "lifecycle", "economics", "goals"].includes(view))
      ? { agent_id: agentId }
      : {}),
  };
  const contextTitle =
    context.context_type === "execution"
      ? `Execução ${execution?.incident_id || context.execution_id}`
      : context.context_type === "knowledge"
        ? `Conhecimento ${item?.title || context.knowledge_id}`
        : context.context_type === "recommendation"
          ? "Recomendação em revisão"
          : context.agent_id
            ? `Agente ${names[context.agent_id] || context.agent_id}`
            : "Workforce";
  const openMaestro = () => {
    setMaestroOverride(null);
    setMaestroOpen(true);
  };
  const maestroPanel = (
    <MaestroPanel
      chat={chat}
      context={context}
      title={contextTitle}
      lifecycle={
        context.agent_id
          ? data?.agents.find((a) => a.registry.agent_id === context.agent_id)
              ?.registry.lifecycle_state
          : undefined
      }
      attention={data?.attention.agent_ids}
      onClose={maestroOpen ? () => setMaestroOpen(false) : undefined}
      onKnowledge={(id) => {
        setKnowledgeId(id);
        setView("knowledge");
        setMaestroOverride(null);
      }}
    />
  );

  async function action<T>(
    name: string,
    fn: () => Promise<T>,
    done: (result: T) => void,
  ) {
    setBusy(name);
    setToast("");
    try {
      done(await fn());
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Não foi possível concluir.");
    } finally {
      setBusy("");
    }
  }
  const openExecution = (id: string) =>
    action(
      "execution",
      () => api<Detail>("cockpit/executions/" + id + "?source=" + source),
      (e) => {
        setExecution(e);
        setView("operations");
      },
    );
  const extract = () =>
    execution &&
    action(
      "extract",
      () =>
        api<Knowledge>(
          "knowledge/extract/" + execution.execution_id + "?source=" + source,
          {},
        ),
      (k) => {
        setKnowledgeId(k.id);
        setView("knowledge");
        setExecution(null);
        refresh();
      },
    );
  const review = (status: "approve" | "reject") =>
    item &&
    action(
      "review",
      () =>
        api<Knowledge>("knowledge/" + item.id + "/" + status, {
          reviewer,
          note: reviewNote,
          confirmed,
        }),
      () => {
        setToast(
          status === "approve"
            ? "Conhecimento aprovado e persistido."
            : "Candidato rejeitado e persistido.",
        );
        setConfirmed(false);
        setReviewer("");
        setReviewNote("");
        refresh();
      },
    );
  const sourceBadge = (
    <Badge value={source}>
      {source === "didactic"
        ? "DIDÁTICO · DADOS SINTÉTICOS"
        : "HISTÓRICO · DADOS PERSISTIDOS"}
    </Badge>
  );
  const workforce = (agents: Agent[]) =>
    agents.length ? (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Agente</th>
              <th>Lifecycle</th>
              <th>Meta</th>
              <th>Qualidade*</th>
              <th>SLO</th>
              <th>Custo LLM</th>
              <th>Recomendação</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr
                key={a.registry.agent_id}
                onClick={() => openAgent(a.registry.agent_id)}
                tabIndex={0}
                role="button"
                aria-label={"Abrir agente " + a.name_pt}
                onKeyDown={(e) =>
                  e.key === "Enter" && openAgent(a.registry.agent_id)
                }
              >
                <td>
                  <div className="agent-cell">
                    <span className="avatar">{a.name_pt.slice(0, 2)}</span>
                    <div>
                      <b>{a.name_pt}</b>
                      <small>{label(a.registry.status)}</small>
                    </div>
                  </div>
                </td>
                <td>
                  <Badge value={a.registry.lifecycle_state} />
                </td>
                <td>
                  <b>{num(a.goals[0].actual, "%")}</b>
                  <small>{label(a.goals[0].status)}</small>
                </td>
                <td>
                  {num(a.quality.observed, "%")}
                  <small>Resultado não normal</small>
                </td>
                <td>
                  <div className="inline wrap">
                    {a.slos.map((s) => (
                      <span
                        title={s.slo_id + " · " + label(s.status)}
                        key={s.slo_id}
                        className={"dot " + s.status}
                      />
                    ))}
                  </div>
                </td>
                <td>{num(a.economics.observed, "USD")}</td>
                <td>
                  {a.recommendation ? (
                    <Badge value={a.recommendation.action} />
                  ) : (
                    <span className="muted">Sem proposta</span>
                  )}
                </td>
                <td>
                  <ChevronRight size={16} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <Empty />
    );
  const goals = (agents: Agent[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Agente / meta</th>
            <th>Alvo</th>
            <th>Atual</th>
            <th>Gap</th>
            <th>Tendência</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {agents.flatMap((a) =>
            a.goals.map((g) => (
              <tr key={g.goal_id}>
                <td>
                  <b>{a.name_pt}</b>
                  <small>{a.registry.business_goals[0].name}</small>
                  <small>
                    {source === "didactic"
                      ? "Evidência didática"
                      : "Histórico durável"}{" "}
                    · {a.sample_count} amostras
                  </small>
                </td>
                <td>{num(g.target, "%")}</td>
                <td>{num(g.actual, "%")}</td>
                <td>{num(g.gap, "p.p.")}</td>
                <td>{label(a.goal_trend)}</td>
                <td>
                  <Badge value={g.status} />
                </td>
              </tr>
            )),
          )}
        </tbody>
      </table>
    </div>
  );
  const slos = (a: Agent) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Limite operacional</th>
            <th>Observado</th>
            <th>Alvo</th>
            <th>Situação</th>
          </tr>
        </thead>
        <tbody>
          {a.slos.map((s) => (
            <tr key={s.slo_id}>
              <td>
                {(
                  {
                    "stage-completion": "Conclusão / cobertura",
                    "stage-latency": "Latência p95 (ms)",
                    "stage-llm-cost": "Custo LLM (USD)",
                    "workflow-degradation": "Resultados degradados (%)",
                  } as Record<string, string>
                )[s.slo_id] || s.slo_id}
              </td>
              <td>{num(s.observed)}</td>
              <td>
                {s.operator} {num(s.target)}
              </td>
              <td>
                <Badge value={s.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  const lifecycle = (a: Agent) => (
    <>
      <LifecycleGraph
        edges={data?.settings.lifecycle_edges || []}
        current={a.registry.lifecycle_state}
      />
      <p className="notice">
        Cadastro ≠ lifecycle ≠ saúde do runtime ≠ estado da execução. Nenhuma
        transição é executada pelo cockpit.
      </p>
      {a.recommendation && (
        <Panel title="Transição recomendada · não executada">
          <p>Aprovação humana: obrigatória.</p>
          <Decision r={a.recommendation} />
        </Panel>
      )}
    </>
  );
  const economy = (a: Agent) => (
    <div className="split">
      <Panel title="Custo da IA" tag="ESTIMADO">
        <div className="big-number">{num(a.economics.observed, "USD")}</div>
        <p>
          Usage registrado e atribuído ao papel. Não representa o custo total do
          agente.
        </p>
        <p className="muted">Tendência: {label(a.cost_trend)}</p>
        <div className="kv">
          <span>Custo total da execução</span>
          <b>Não disponível</b>
        </div>
        <small>
          Infraestrutura e trabalho humano não medidos. Não confundir custo LLM
          com custo total.
        </small>
      </Panel>
      <Panel title="Valor de negócio" tag="PARCIAL">
        <h3>Valor realizado: ainda não validado</h3>
        {data?.business_exposure.exposure_brl && (
          <div className="value-exposure">
            <small>CENÁRIO DIDÁTICO · INCIDENT-001</small>
            <span>Exposição potencial / valor sob gestão</span>
            <strong>{money(data.business_exposure.exposure_brl)}</strong>
            <p>
              {money(data.business_exposure.daily_penalty_brl)} / dia ×{" "}
              {data.business_exposure.hypothetical_days} dias hipotéticos.
            </p>
            <small>
              Pedido CO-001 · não é economia realizada nem impacto confirmado.
              Contexto do incidente; não somar entre agentes.
            </small>
          </div>
        )}
        <p>
          Cenário recomendado e tempo até proposta são contexto; status:
          aguardando aprovação.
        </p>
        {a.business_value.slice(0, 3).map((v, i) => (
          <div className="kv" key={i}>
            <span>{label(v.value_metric)}</span>
            <b>
              {v.currency_or_unit === "BRL"
                ? money(v.value_amount)
                : num(
                    v.value_amount,
                    v.currency_or_unit === "unknown" ? "" : v.currency_or_unit,
                  )}
            </b>
          </div>
        ))}
        <small>
          LLM Cost ≠ Agent Cost ≠ Workflow Cost ≠ Business Decision ≠ Business
          Value. Sem conversão automática de moedas ou ROI.
        </small>
      </Panel>
    </div>
  );
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img
            className="official-logo"
            src="/l3-logo.jpg"
            width="285"
            height="167"
            alt="Logo oficial L3"
          />
          <div>
            <strong>L3 Control Plane</strong>
            <small>AGENTIC WORKFORCE OPERATIONS</small>
          </div>
        </div>
        <div className="workspace">
          <span className="workspace-icon">N</span>
          <div>
            <b>NovaCore</b>
            <small>Laboratório de operações</small>
          </div>
          <Badge>LAB</Badge>
        </div>
        <div className="nav-label">ESPAÇO DE OPERAÇÕES</div>
        <nav>
          {nav.map(([id, title, Icon], i) => (
            <button
              key={id}
              className={
                (view === id ? "active " : "") + (i === 9 ? "nav-divider" : "")
              }
              onClick={() => go(id)}
            >
              <Icon size={17} />
              <span>{title}</span>
              {id === "alerts" && data && data.overview.alerts > 0 && (
                <em>{data.overview.alerts}</em>
              )}
              {id === "maestro" && <span className="ai-chip">IA</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <ShieldCheck size={16} />
          <div>
            <b>Autonomia com limites</b>
            <small>Recomendar. Revisar. Aprender.</small>
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="breadcrumb">
            Workforce <ChevronRight size={13} />
            <b>{nav.find((n) => n[0] === view)?.[1]}</b>
          </div>
          <div className="inline gap">
            <Button onClick={openMaestro}>Perguntar ao Maestro</Button>
            <span className="live-label">
              <i /> Ambiente local
            </span>
            <button
              className="icon-button"
              aria-label="Atualizar dados"
              onClick={refresh}
            >
              <RefreshCw size={17} />
            </button>
            <span className="user-avatar">LL</span>
          </div>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">L3 CONTROL PLANE / AULA 4</div>
              <h1>
                {view === "overview"
                  ? "Uma visão da sua força de trabalho."
                  : agentOpen && current
                    ? current.name_pt
                    : nav.find((n) => n[0] === view)?.[1]}
              </h1>
              <p>
                {view === "overview"
                  ? "Da execução isolada à coordenação de uma organização agêntica."
                  : "Evidências primeiro. Decisões explícitas. Conhecimento com proveniência."}
              </p>
            </div>
            <div className="source-control">
              <label htmlFor="source">Fonte de dados</label>
              <select
                id="source"
                value={source}
                disabled={!!busy}
                onChange={(e) => {
                  setData(null);
                  setLoading(true);
                  setDecision(null);
                  setSource(e.target.value as Source);
                  setExecution(null);
                  setKnowledgeId(null);
                }}
              >
                <option value="didactic">Cenário didático</option>
                <option value="durable">Histórico persistido</option>
              </select>
              {data && (
                <small>
                  Modo do serviço: {data.runtime_mode} · {date(data.updated_at)}
                </small>
              )}
            </div>
          </div>
          <div className="source-line">
            {sourceBadge}
            <span>
              {source === "didactic"
                ? "Cenário sintético: Supply tem 50 observações de cobertura; a lista de 6 execuções é ilustrativa e independente."
                : "Projeções calculadas a partir do histórico existente. Ausências permanecem desconhecidas."}
            </span>
          </div>
          {toast && (
            <div role="status" className="toast">
              {toast}
              <button aria-label="Fechar mensagem" onClick={() => setToast("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {loading && !data ? (
            <div role="status" className="loading">
              <Loader2 className="spin" /> Carregando a força de trabalho…
            </div>
          ) : error ? (
            <Panel>
              <div role="alert">
                <h3>Não foi possível carregar o cockpit</h3>
                <p>{error}</p>
                <Button onClick={refresh}>Tentar novamente</Button>
              </div>
            </Panel>
          ) : (
            data && (
              <>
                {view === "overview" && (
                  <>
                    <div className="performance-heading">
                      <h2>Performance da workforce</h2>
                      <span>
                        {data.overview.alerts} alertas ·{" "}
                        {data.overview.pending_recommendations} recomendações
                        abertas
                      </span>
                    </div>
                    {data.attention.count > 0 && (
                      <button
                        className="attention-cta"
                        onClick={() => {
                          const ids = data.attention.agent_ids;
                          setMaestroOverride({
                            context_type:
                              ids.length === 1 ? "agent" : "workforce",
                            ...(ids.length === 1 ? { agent_id: ids[0] } : {}),
                            source,
                            route: "overview",
                          });
                          chat.setQuestion(
                            ids.length === 1
                              ? `Por que o agente de ${names[ids[0]]} requer atenção e como posso melhorá-lo?`
                              : "Quais agentes requerem atenção e como posso melhorá-los?",
                          );
                          setMaestroOpen(true);
                        }}
                      >
                        {data.attention.label} · Perguntar ao Maestro ↗
                      </button>
                    )}
                    <div className="value-strip">
                      <div>
                        <small>VALOR SOB GESTÃO · {label(source)}</small>
                        <b>{money(data.business_exposure.exposure_brl)}</b>
                        <span>
                          Exposição potencial; não é economia realizada
                        </span>
                      </div>
                      <div>
                        <small>VALOR REALIZADO</small>
                        <b>Não validado</b>
                        <span>Propostas aguardam decisão humana</span>
                      </div>
                    </div>
                    <div className="kpis">
                      <Panel>
                        <div className="metric-label">
                          Agentes ativos <Users size={17} />
                        </div>
                        <strong>
                          {data.overview.active_agents}
                          <span> / {data.overview.total_agents}</span>
                        </strong>
                        <small>Identidade e responsabilidade definidas</small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">
                          Metas dentro do alvo <Target size={17} />
                        </div>
                        <strong>
                          {data.overview.goals.on_target}
                          <span> agentes</span>
                        </strong>
                        <small>
                          {data.overview.goals.off_target} fora da meta ·{" "}
                          {data.overview.goals.unknown} desconhecidas
                        </small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">
                          Atenção necessária <Bell size={17} />
                        </div>
                        <strong>
                          {data.overview.attention_agents}
                          <span> em atenção</span>
                        </strong>
                        <small>
                          {data.overview.alerts} sinais para investigação
                        </small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">
                          Propostas pendentes <GitBranch size={17} />
                        </div>
                        <strong>{data.overview.pending_recommendations}</strong>
                        <small>Aprovação humana obrigatória</small>
                      </Panel>
                    </div>
                    <div className="overview-grid">
                      <Panel
                        title="Desempenho frente às metas"
                        tag="META × ATUAL"
                      >
                        <div className="chart-legend">
                          <span>
                            <i />
                            Resultado
                          </span>
                          <span>
                            <i />
                            Alvo
                          </span>
                        </div>
                        <div className="chart">
                          <ResponsiveContainer width="100%" height={230}>
                            <BarChart data={data.chart} barGap={5}>
                              <CartesianGrid
                                vertical={false}
                                stroke="var(--line)"
                              />
                              <XAxis
                                dataKey="agent"
                                interval={0}
                                tickFormatter={(v: string) =>
                                  v === "Supervisor de operações"
                                    ? "Supervisor"
                                    : v === "Riscos e contestação"
                                      ? "Contestação"
                                      : v
                                }
                                tick={{ fontSize: 10, fill: "var(--muted)" }}
                                axisLine={false}
                                tickLine={false}
                              />
                              <YAxis
                                domain={[0, 100]}
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={false}
                                unit="%"
                                width={40}
                              />
                              <Tooltip
                                formatter={(v) => num(v as number, "%")}
                                contentStyle={{
                                  borderRadius: 10,
                                  border: "1px solid var(--line)",
                                }}
                              />
                              <Bar
                                isAnimationActive={false}
                                dataKey="actual"
                                name="Atual"
                                fill="var(--chart-result)"
                                radius={[5, 5, 0, 0]}
                              />
                              <Bar
                                isAnimationActive={false}
                                dataKey="target"
                                name="Alvo"
                                fill="var(--chart-target)"
                                radius={[5, 5, 0, 0]}
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                        <small>
                          Metas técnicas diferentes por papel. Este gráfico não
                          é um ranking de inteligência.
                        </small>
                      </Panel>
                      <section className="spotlight">
                        <div className="eyebrow">
                          <Sparkles size={14} /> UMA DECISÃO, COM CONTEXTO
                        </div>
                        <h2>
                          Da evidência
                          <br />à próxima melhoria.
                        </h2>
                        <p>
                          Reúna metas, sinais e conhecimento validado antes de
                          propor uma intervenção.
                        </p>
                        <Button
                          onClick={() => {
                            setAgentId("supply");
                            go("maestro");
                          }}
                        >
                          Conversar com o Maestro <ArrowUpRight size={16} />
                        </Button>
                        <div className="spotlight-footer">
                          <ShieldCheck size={15} /> O humano permanece na
                          decisão.
                        </div>
                      </section>
                    </div>
                    <Panel
                      title="Agentic Workforce"
                      tag="REGISTRY + METAS + SINAIS"
                    >
                      {workforce(data.agents)}
                    </Panel>
                    <div className="split">
                      <Panel title="Sinais operacionais">
                        <div className="kv">
                          <span>Valor de negócio realizado</span>
                          <b>Desconhecido</b>
                        </div>
                        <div className="kv">
                          <span>Violações de SLO</span>
                          <b>{data.overview.slo_violations}</b>
                        </div>
                        <div className="kv">
                          <span>Execuções degradadas na lista</span>
                          <b>{data.overview.degraded_executions}</b>
                        </div>
                        <div className="kv">
                          <span>Custo LLM estimado</span>
                          <b>{num(data.overview.estimated_cost_usd, "USD")}</b>
                        </div>
                        <small>{data.overview.cost_window}</small>
                      </Panel>
                      <Panel title="Memória em construção">
                        <div className="kv">
                          <span>Conhecimento validado</span>
                          <b>{data.knowledge.counts.approved}</b>
                        </div>
                        <div className="kv">
                          <span>Aguardando revisão</span>
                          <b>{data.knowledge.counts.pending_review}</b>
                        </div>
                        <Button variant="ghost" onClick={() => go("knowledge")}>
                          Explorar o Segundo Cérebro <ArrowRight size={15} />
                        </Button>
                      </Panel>
                    </div>
                  </>
                )}
                {view === "agents" && !agentOpen && (
                  <Panel title="Agentes e responsabilidades">
                    {workforce(data.agents)}
                  </Panel>
                )}
                {view === "agents" && agentOpen && current && (
                  <>
                    <div className="agent-hero">
                      <span className="large-avatar">
                        {current.name_pt.slice(0, 2)}
                      </span>
                      <div>
                        <div className="inline gap">
                          <h2>{current.name_pt}</h2>
                          <Badge value={current.registry.lifecycle_state} />
                          <Badge value={current.registry.status} />
                        </div>
                        <p>{roles[current.registry.agent_id]}</p>
                        <small>
                          {owners[current.registry.business_owner] ||
                            current.registry.business_owner}{" "}
                          · {current.registry.version}
                        </small>
                      </div>
                      <Button variant="outline" onClick={openMaestro}>
                        Perguntar ao Maestro <Sparkles size={16} />
                      </Button>
                    </div>
                    <div className="tabs">
                      {[
                        "Resumo",
                        "Metas",
                        "Execuções",
                        "Qualidade",
                        "Economia",
                        "SLOs",
                        "Lifecycle",
                        "Decisões",
                        "Conhecimento",
                      ].map((t) => (
                        <button
                          key={t}
                          onClick={() => setTab(t)}
                          className={tab === t ? "selected" : ""}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                    {tab === "Resumo" && (
                      <div className="split">
                        <Panel title="Identidade e governança">
                          {[
                            ["Identificador", current.registry.agent_id],
                            [
                              "Responsável de negócio",
                              owners[current.registry.business_owner] ||
                                current.registry.business_owner,
                            ],
                            [
                              "Responsável técnico",
                              owners[current.registry.technical_owner] ||
                                current.registry.technical_owner,
                            ],
                            [
                              "Criticidade",
                              label(current.registry.criticality),
                            ],
                            ["Versão", current.registry.version],
                          ].map(([k, v]) => (
                            <div className="kv" key={k}>
                              <span>{k}</span>
                              <b>{v}</b>
                            </div>
                          ))}
                        </Panel>
                        <Panel title="Capacidades">
                          <div className="kv">
                            <span>Execução</span>
                            <b>{label(current.registry.execution_type)}</b>
                          </div>
                          <div className="kv">
                            <span>Modelo</span>
                            <b>{current.registry.model || "Sem modelo LLM"}</b>
                          </div>
                          <h4>Ferramentas</h4>
                          <div className="chips">
                            {current.registry.tools.map((t) => (
                              <code key={t}>{t}</code>
                            ))}
                          </div>
                          <h4>Interfaces</h4>
                          <div className="chips">
                            {current.registry.interfaces.map((t) => (
                              <code key={t}>{t}</code>
                            ))}
                          </div>
                          <p className="notice">
                            Cadastrado e ativo não significam saudável agora.
                            Saúde individual não medida.
                          </p>
                        </Panel>
                      </div>
                    )}
                    {tab === "Metas" && <Panel>{goals([current])}</Panel>}
                    {tab === "SLOs" && <Panel>{slos(current)}</Panel>}
                    {tab === "Lifecycle" && lifecycle(current)}
                    {data.plans
                      .filter((p) => p.agent_id === agentId)
                      .slice(0, 1)
                      .map((p) => (
                        <Panel
                          key={p.plan_id}
                          title="Última análise do Maestro"
                        >
                          <h3>Problema observado</h3>
                          <p>{p.diagnosis}</p>
                          <h4>Hipótese a verificar</h4>
                          <p>
                            {p.hypothesis ||
                              "Causa ainda não estabelecida; revisar as evidências da proposta."}
                          </p>
                          <h4>Recomendação</h4>
                          <p>{p.objective}</p>
                          <p>
                            Staffs:{" "}
                            {p.staff_assignments.map((s) => s.name).join(" · ")}
                          </p>
                          <Badge value={p.status} />
                          <Button variant="outline" onClick={openMaestro}>
                            Continuar conversa no Maestro
                          </Button>
                        </Panel>
                      ))}
                    {tab === "Decisões" &&
                      (current.recommendation ? (
                        <Panel>
                          <Decision r={current.recommendation} />
                        </Panel>
                      ) : (
                        <Empty title="Sem recomendação sustentada" />
                      ))}
                    {tab === "Economia" && economy(current)}
                    {tab === "Qualidade" && (
                      <Panel title="Qualidade é um vetor">
                        <div className="big-number">
                          {num(current.quality.observed, "%")}
                        </div>
                        <p>
                          Resultados não normais no contexto do workflow. Não é
                          uma nota de qualidade do agente.
                        </p>
                        <p className="notice">
                          Completude semântica e conformidade não são
                          certificadas por uma etapa concluída.
                        </p>
                      </Panel>
                    )}
                    {tab === "Execuções" && (
                      <Panel title="Execuções da fonte selecionada">
                        <p>
                          Contexto operacional compartilhado; não representa
                          atribuição causal ao agente.
                        </p>
                        {data.operations.slice(0, 8).map((o) => (
                          <button
                            className="list-button"
                            key={o.execution_id}
                            onClick={() => openExecution(o.execution_id)}
                          >
                            <span>
                              {o.incident_id} · {o.execution_id.slice(0, 8)}
                            </span>
                            <Badge value={o.status} />
                          </button>
                        ))}
                      </Panel>
                    )}
                    {tab === "Conhecimento" && (
                      <Panel title="Conhecimento relacionado">
                        {data.knowledge.items
                          .filter((k) => k.tags.includes(agentId))
                          .map((k) => (
                            <button
                              className="list-button"
                              key={k.id}
                              onClick={() => {
                                setKnowledgeId(k.id);
                                setView("knowledge");
                              }}
                            >
                              {k.title}
                              <Badge value={k.validation_status} />
                            </button>
                          ))}
                      </Panel>
                    )}
                  </>
                )}
                {view === "goals" && (
                  <Panel title="Metas como contratos de desempenho">
                    {goals(data.agents)}
                  </Panel>
                )}
                {view === "operations" && !execution && (
                  <Panel title="População operacional">
                    <div className="toolbar">
                      <Search size={16} />
                      <input
                        aria-label="Filtrar execuções"
                        placeholder="Filtrar por incidente, status ou UUID"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </div>
                    {data.operations.length ? (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Incidente / execução</th>
                              <th>Status</th>
                              <th>Resultado</th>
                              <th>Duração</th>
                              <th>Aprovação</th>
                              <th>Criada em</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.operations
                              .filter((o) =>
                                (
                                  o.incident_id +
                                  o.execution_id +
                                  label(o.status)
                                )
                                  .toLowerCase()
                                  .includes(query.toLowerCase()),
                              )
                              .map((o) => (
                                <tr
                                  key={o.execution_id}
                                  tabIndex={0}
                                  role="button"
                                  aria-label={
                                    "Abrir execução " + o.execution_id
                                  }
                                  onClick={() => openExecution(o.execution_id)}
                                  onKeyDown={(e) =>
                                    e.key === "Enter" &&
                                    openExecution(o.execution_id)
                                  }
                                >
                                  <td>
                                    <b>{o.incident_id}</b>
                                    <small>
                                      {o.execution_id.slice(0, 12)}…
                                    </small>
                                  </td>
                                  <td>
                                    <Badge value={o.status} />
                                  </td>
                                  <td>{label(o.outcome)}</td>
                                  <td>{num(o.duration_ms, "ms")}</td>
                                  <td>{label(o.approval_status)}</td>
                                  <td>{date(o.created_at)}</td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <Empty title="Nenhuma execução persistida" />
                    )}
                  </Panel>
                )}
                {view === "operations" && execution && (
                  <>
                    <div className="inline between">
                      <div>
                        <h2>{execution.incident_id}</h2>
                        <small>{execution.execution_id}</small>
                      </div>
                      <Button
                        disabled={!!busy || execution.status !== "completed"}
                        onClick={extract}
                      >
                        {busy === "extract" ? (
                          <Loader2 className="spin" size={16} />
                        ) : (
                          <BrainCircuit size={16} />
                        )}{" "}
                        Extrair aprendizado
                      </Button>
                    </div>
                    <div className="split">
                      <Panel title="Resultado e revisão">
                        <Badge value={execution.outcome} />
                        <p>
                          {source === "didactic"
                            ? "Proposta ilustrativa do caso NovaCore. Nenhuma ação foi executada."
                            : execution.result.action ||
                              "Resultado ainda indisponível."}
                        </p>
                        <div className="kv">
                          <span>Iniciada em</span>
                          <b>{date(execution.started_at)}</b>
                        </div>
                        <div className="kv">
                          <span>Concluída em</span>
                          <b>{date(execution.completed_at)}</b>
                        </div>
                        <div className="kv">
                          <span>Worker responsável</span>
                          <b>{execution.worker_id || "Não registrado"}</b>
                        </div>
                        <div className="kv">
                          <span>Duração</span>
                          <b>{num(execution.duration_ms, "ms")}</b>
                        </div>
                        <div className="kv">
                          <span>Aprovação</span>
                          <Badge
                            value={execution.result.approval || "unknown"}
                          />
                        </div>
                        <p className="notice">
                          Concluída é status de runtime. Não é sinônimo de
                          qualidade.
                        </p>
                        {execution.trace_id && (
                          <a
                            className="text-link"
                            href={
                              "http://localhost:16686/trace/" +
                              execution.trace_id
                            }
                            target="_blank"
                            rel="noreferrer"
                          >
                            Abrir trace no Jaeger ↗
                          </a>
                        )}
                      </Panel>
                      <Panel title="Economia desta execução">
                        <p className="notice">
                          {source === "didactic"
                            ? "Valores sintéticos do cenário. Nenhum consumo real de provider."
                            : label(execution.economics.cost_source)}
                        </p>
                        {[
                          ["Chamadas LLM", execution.economics.llm_calls],
                          [
                            "Tokens de entrada",
                            execution.economics.input_tokens,
                          ],
                          [
                            "Tokens de saída",
                            execution.economics.output_tokens,
                          ],
                          ["Tokens em cache", null],
                          ["Retries", execution.economics.retry_count],
                          [
                            "Custo LLM estimado (USD)",
                            execution.economics.estimated_llm_cost,
                          ],
                        ].map(([k, v]) => (
                          <div className="kv" key={String(k)}>
                            <span>{k}</span>
                            <b>{num(v as string | number | null)}</b>
                          </div>
                        ))}
                        <small>
                          {execution.economics.pricing_version ||
                            "Sem referência aplicada"}{" "}
                          ·{" "}
                          {execution.economics.reference_date ||
                            "Data indisponível"}
                        </small>
                      </Panel>
                    </div>
                    <Panel title="Qualidade, sem score artificial">
                      <div className="quality-cards">
                        {[
                          ["Fallback", execution.quality.fallback_used],
                          [
                            "Revisão humana",
                            execution.quality.human_review_required,
                          ],
                          [
                            "Evidências completas",
                            execution.quality.evidence_complete,
                          ],
                          ["Conformidade", execution.quality.policy_compliant],
                        ].map(([k, v]) => (
                          <div key={String(k)}>
                            <small>{k}</small>
                            <b>
                              {v == null ? "Desconhecido" : v ? "Sim" : "Não"}
                            </b>
                          </div>
                        ))}
                      </div>
                      <small>
                        Confiança do workflow:{" "}
                        {num(execution.quality.confidence)} · valor não
                        calibrado, não probabilidade de sucesso.
                      </small>
                    </Panel>
                    <Panel title="Linha do tempo registrada">
                      <div className="workflow-legend">
                        Incidente → Supervisor → Suprimentos / Produção /
                        Logística → Finanças → Contestação → Recomendação →
                        Aprovação humana
                      </div>
                      <div className="timeline">
                        {execution.events.map((e) => (
                          <div key={e.id}>
                            <span className="timeline-dot" />
                            <div>
                              <b>
                                {names[e.agent] || "Runtime"} ·{" "}
                                {e.type.endsWith(".completed")
                                  ? "concluído"
                                  : e.type.endsWith(".failed")
                                    ? "falha registrada"
                                    : e.type.endsWith(".started")
                                      ? "iniciado"
                                      : e.type === "llm.fallback_activated"
                                        ? "fallback ativado"
                                        : e.type === "llm.retry"
                                          ? "nova tentativa"
                                          : "evento registrado"}
                              </b>
                              <small>
                                {date(e.timestamp)} · {e.type}
                              </small>
                            </div>
                          </div>
                        ))}
                      </div>
                    </Panel>
                  </>
                )}
                {view === "quality" && (
                  <>
                    <div className="banner">
                      <ShieldCheck />
                      <div>
                        <h3>Qualidade é um vetor antes de ser uma nota.</h3>
                        <p>
                          Resultados, degradação, revisão e limites da evidência
                          são dimensões diferentes.
                        </p>
                      </div>
                    </div>
                    <Panel>
                      {data.agents.map((a) => (
                        <div className="kv" key={a.registry.agent_id}>
                          <b>{a.name_pt}</b>
                          <span>
                            Resultados não normais no contexto:{" "}
                            {num(a.quality.observed, "%")}
                          </span>
                          <Button
                            variant="ghost"
                            onClick={() => openAgent(a.registry.agent_id)}
                          >
                            Explorar <ArrowRight size={14} />
                          </Button>
                        </div>
                      ))}
                    </Panel>
                  </>
                )}
                {view === "economics" && current && (
                  <>
                    {economy(current)}
                    <Panel
                      title="Referência pública de pricing"
                      tag="CONFIGURADO"
                    >
                      {Object.entries(data.settings.pricing.models).map(
                        ([model, p]) => (
                          <div key={model}>
                            <h3>{model}</h3>
                            <div className="quality-cards">
                              <div>
                                <small>Entrada / 1M tokens</small>
                                <b>USD {num(p.input_per_million)}</b>
                              </div>
                              <div>
                                <small>Entrada em cache / 1M</small>
                                <b>USD {num(p.cached_input_per_million)}</b>
                              </div>
                              <div>
                                <small>Saída / 1M tokens</small>
                                <b>USD {num(p.output_per_million)}</b>
                              </div>
                              <div>
                                <small>Referência</small>
                                <b>{data.settings.pricing.reference_date}</b>
                              </div>
                            </div>
                          </div>
                        ),
                      )}
                      <p className="notice">
                        Usage do provider = medido · Pricing = configurado ·
                        Custo = estimado. Cache não medido não recebe desconto
                        inventado.
                      </p>
                    </Panel>
                    <Panel title="Custo na janela consultada">
                      <div className="big-number">
                        {num(data.overview.estimated_cost_usd, "USD")}
                      </div>
                      <p>
                        {data.overview.cost_window}.{" "}
                        {data.overview.cost_sample_count} execuções consultadas.
                      </p>
                    </Panel>
                  </>
                )}
                {view === "decisions" && (
                  <Panel title="Recomendações do Control Plane">
                    {data.recommendations.length ? (
                      data.recommendations.map((r) => (
                        <button
                          className="decision-row"
                          key={r.recommendation_id}
                          onClick={() => setDecision(r)}
                        >
                          <span className="avatar">
                            <GitBranch size={18} />
                          </span>
                          <div>
                            <b>
                              {names[r.agent_id]} · {label(r.action)}
                            </b>
                            <small>{r.reason_pt}</small>
                          </div>
                          <Badge value={r.priority} />
                          <ChevronRight size={17} />
                        </button>
                      ))
                    ) : (
                      <Empty
                        title="Nenhuma recomendação sustentada"
                        text="Dados ausentes não são interpretados como sucesso ou autorização para escalar."
                      />
                    )}
                  </Panel>
                )}
                {view === "alerts" && (
                  <Panel title="Sinais que merecem atenção">
                    {data.alerts.length ? (
                      data.alerts.map((a) => (
                        <div className="decision-row" key={a.id}>
                          <Bell size={20} />
                          <div>
                            <b>
                              {names[a.agent_id]} · {a.message}
                            </b>
                            <small>
                              {date(a.timestamp)} · {label(a.source)} ·{" "}
                              {a.recommendation
                                ? label(a.recommendation)
                                : "Sem proposta"}
                            </small>
                          </div>
                          <Badge value={a.severity} />
                        </div>
                      ))
                    ) : (
                      <Empty title="Sem alertas nesta fonte" />
                    )}
                  </Panel>
                )}
                {view === "lifecycle" && current && (
                  <>
                    <select
                      aria-label="Agente para lifecycle"
                      value={agentId}
                      onChange={(e) => setAgentId(e.target.value)}
                    >
                      {data.agents.map((a) => (
                        <option
                          key={a.registry.agent_id}
                          value={a.registry.agent_id}
                        >
                          {a.name_pt}
                        </option>
                      ))}
                    </select>
                    {lifecycle(current)}
                  </>
                )}
                {view === "maestro" && !maestroOpen && (
                  <Panel className="chat">{maestroPanel}</Panel>
                )}
                {view === "knowledge" && !item && (
                  <>
                    <div className="kpis">
                      <Panel>
                        <div className="metric-label">
                          Conhecimento validado
                        </div>
                        <strong>{data.knowledge.counts.approved}</strong>
                        <small>Fonte: {label(source)}</small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">Aguardando revisão</div>
                        <strong>{data.knowledge.counts.pending_review}</strong>
                        <small>Não utilizado como verdade aprovada</small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">Substituído</div>
                        <strong>{data.knowledge.counts.superseded}</strong>
                        <small>Histórico preservado</small>
                      </Panel>
                      <Panel>
                        <div className="metric-label">
                          Tipos de conhecimento
                        </div>
                        <strong>4</strong>
                        <small>
                          Entidades · decisões · aprendizados · padrões
                        </small>
                      </Panel>
                    </div>
                    <Panel
                      title="Navegar pelo conhecimento"
                      tag="MARKDOWN + PROVENIÊNCIA"
                    >
                      <div className="toolbar">
                        <Search size={17} />
                        <input
                          aria-label="Buscar conhecimento"
                          placeholder="Buscar título ou conteúdo"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                        />
                      </div>
                      {data.knowledge.items.length ? (
                        data.knowledge.items
                          .filter((k) =>
                            (k.title + k.content)
                              .toLowerCase()
                              .includes(query.toLowerCase()),
                          )
                          .map((k) => (
                            <button
                              className="knowledge-row"
                              key={k.id}
                              onClick={() => setKnowledgeId(k.id)}
                            >
                              <span className="knowledge-icon">
                                <BookOpen size={19} />
                              </span>
                              <div>
                                <small>
                                  {label(k.type)} · {date(k.updated_at)}
                                </small>
                                <b>{k.title}</b>
                                <p>{k.summary}</p>
                              </div>
                              <Badge value={k.validation_status} />
                              <ChevronRight size={17} />
                            </button>
                          ))
                      ) : (
                        <Empty
                          title="Ainda não há conhecimento nesta fonte"
                          text="Abra uma execução concluída e selecione Extrair aprendizado."
                        />
                      )}
                    </Panel>
                    <Panel
                      title="Mapa de conhecimento"
                      tag="LINKS ENTRE DOCUMENTOS"
                    >
                      <KnowledgeGraph
                        data={data.knowledge}
                        onOpen={setKnowledgeId}
                      />
                    </Panel>
                    <Panel title="O que a organização está aprendendo?">
                      {data.knowledge.items.slice(0, 6).map((k) => (
                        <div className="feed-row" key={k.id}>
                          <span className="timeline-dot" />
                          <div>
                            <b>
                              {label(k.validation_status)} · {k.title}
                            </b>
                            <small>
                              {date(k.updated_at)} · {label(k.source)}
                            </small>
                          </div>
                        </div>
                      ))}
                    </Panel>
                  </>
                )}
                {view === "knowledge" && item && (
                  <>
                    <Button
                      variant="ghost"
                      onClick={() => setKnowledgeId(null)}
                    >
                      ← Voltar ao Segundo Cérebro
                    </Button>
                    <div className="inline between">
                      <div>
                        <div className="inline gap">
                          <Badge value={item.type} />
                          <Badge value={item.validation_status} />
                          {sourceBadge}
                        </div>
                        <h2>{item.title}</h2>
                        <p>{item.summary}</p>
                      </div>
                      <BookOpen size={32} />
                    </div>
                    <div className="split">
                      <Panel title="Conteúdo e inferência">
                        <div className="markdown">
                          {item.content
                            .split("\n")
                            .map((l, i) =>
                              l.startsWith("# ") ? (
                                <h3 key={i}>{l.slice(2)}</h3>
                              ) : l.startsWith("## ") ? (
                                <h4 key={i}>{l.slice(3)}</h4>
                              ) : (
                                <p key={i}>{l}</p>
                              ),
                            )}
                        </div>
                      </Panel>
                      <div>
                        <Panel title="Proveniência">
                          <div className="kv">
                            <span>Origem</span>
                            <b>{label(item.source)}</b>
                          </div>
                          <div className="kv">
                            <span>Gerado por</span>
                            <b>{item.generated_by}</b>
                          </div>
                          <div className="kv">
                            <span>Incidente</span>
                            <b>{item.source_incident}</b>
                          </div>
                          <small>Execução: {item.source_execution}</small>
                          <p>{item.provenance}</p>
                          <small>Criado {date(item.created_at)}</small>
                          {item.reviewer && (
                            <p>
                              Revisão: {item.reviewer} · {item.review_note}
                            </p>
                          )}
                        </Panel>
                        <Panel title="Evidências verificáveis">
                          <Facts facts={item.evidence} />
                        </Panel>
                      </div>
                    </div>
                    <Panel title="Relações existentes">
                      {item.related.map((id) => (
                        <button
                          className="text-link"
                          key={id}
                          onClick={() => setKnowledgeId(id)}
                        >
                          {data.knowledge.items.find((k) => k.id === id)
                            ?.title || id}{" "}
                          ↗
                        </button>
                      ))}
                    </Panel>
                    {item.validation_status === "pending_review" && (
                      <Panel title="Revisão humana do candidato">
                        <p>
                          O LLM propõe conhecimento. O sistema valida estrutura
                          e proveniência. O humano autoriza conhecimento
                          material.
                        </p>
                        <div className="review-form">
                          <label>
                            Seu nome
                            <input
                              aria-label="Nome do revisor"
                              value={reviewer}
                              onChange={(e) => setReviewer(e.target.value)}
                              placeholder="Responsável pela revisão"
                            />
                          </label>
                          <label>
                            Justificativa
                            <textarea
                              aria-label="Justificativa da revisão"
                              value={reviewNote}
                              onChange={(e) => setReviewNote(e.target.value)}
                              placeholder="Registre os limites e as evidências verificadas"
                            />
                          </label>
                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={confirmed}
                              onChange={(e) => setConfirmed(e.target.checked)}
                            />{" "}
                            Revisei o conteúdo, a origem e os limites desta
                            proposta.
                          </label>
                          <div className="inline gap">
                            <Button
                              disabled={
                                !!busy ||
                                !confirmed ||
                                reviewer.trim().length < 3 ||
                                reviewNote.trim().length < 3
                              }
                              onClick={() => review("approve")}
                            >
                              <Check size={16} /> Confirmar aprovação
                            </Button>
                            <Button
                              variant="outline"
                              disabled={
                                !!busy ||
                                !confirmed ||
                                reviewer.trim().length < 3 ||
                                reviewNote.trim().length < 3
                              }
                              onClick={() => review("reject")}
                            >
                              Rejeitar candidato
                            </Button>
                          </div>
                        </div>
                      </Panel>
                    )}
                  </>
                )}
                {view === "loop" && (
                  <>
                    <section className="loop-hero">
                      <div className="eyebrow">
                        EXPERIÊNCIA → CONTEXTO MELHOR → PRÓXIMA DECISÃO
                      </div>
                      <h2>
                        A organização não aprende
                        <br />
                        apenas porque executou mais.
                      </h2>
                      <p>
                        Ela aprende quando a experiência validada melhora a
                        próxima decisão.
                      </p>
                      <Badge>
                        NÍVEL ATUAL: 1 · RECOMENDAR / 2 · DELEGAÇÃO PROPOSTA
                      </Badge>
                    </section>
                    <div className="loop-nodes">
                      {[
                        "Meta",
                        "Execução",
                        "Resultado",
                        "Medição",
                        "Control Plane",
                        "Maestro",
                        "Plano de melhoria",
                        "Staffs",
                        "Validação humana",
                        "Segundo Cérebro",
                        "Melhor contexto",
                        "Próxima execução",
                      ].map((n, i) => (
                        <div key={n}>
                          <small>{String(i + 1).padStart(2, "0")}</small>
                          <b>{n}</b>
                          <ArrowRight size={15} />
                        </div>
                      ))}
                    </div>
                    <div className="split">
                      <Panel title="Estado visível do aprendizado">
                        <div className="kv">
                          <span>Meta em foco</span>
                          <b>
                            {current?.name_pt} ·{" "}
                            {current
                              ? label(current.goals[0].status)
                              : "Desconhecido"}
                          </b>
                        </div>
                        <div className="kv">
                          <span>Último resultado da fonte</span>
                          <b>{label(data.operations[0]?.outcome)}</b>
                        </div>
                        <div className="kv">
                          <span>Plano do Maestro</span>
                          <b>
                            {data.plans.length
                              ? "Proposta disponível"
                              : "Ainda não proposto"}
                          </b>
                        </div>
                        <div className="kv">
                          <span>Conhecimento validado</span>
                          <b>{data.knowledge.counts.approved}</b>
                        </div>
                        <div className="kv">
                          <span>Aprendizado aguardando revisão</span>
                          <b>{data.knowledge.counts.pending_review}</b>
                        </div>
                        <p className="notice">
                          Próximo passo: revisão humana das propostas. Nenhuma
                          alteração automática de código ou modelo.
                        </p>
                      </Panel>
                      <Panel title="Autonomia com autoridade">
                        <ol className="autonomy">
                          {[
                            "Observar",
                            "Recomendar",
                            "Propor delegação",
                            "Executar com aprovação",
                            "Adaptação controlada",
                            "Aprendizado contínuo",
                          ].map((s, i) => (
                            <li key={s}>
                              <span>{i}</span>
                              <b>{s}</b>
                              <small>
                                {i <= 2
                                  ? "Representado no LAB"
                                  : "Visão futura"}
                              </small>
                            </li>
                          ))}
                        </ol>
                      </Panel>
                    </div>
                    <Panel title="Maturidade da empresa agêntica">
                      <div className="maturity-track">
                        {[
                          ["Automação", "Agentes executam tarefas."],
                          [
                            "Observável",
                            "Execuções possuem telemetria, histórico e qualidade operacional.",
                          ],
                          [
                            "Gerenciada",
                            "Identidade, metas, SLOs, economics e lifecycle.",
                          ],
                          [
                            "Adaptativa",
                            "Control Plane identifica gaps. Maestro propõe melhorias. Segundo Cérebro preserva conhecimento.",
                          ],
                          [
                            "Learning Enterprise",
                            "Experiência, conhecimento, feedback e melhoria formam um ciclo contínuo.",
                          ],
                        ].map(([name, description], i) => (
                          <div key={name}>
                            <span>{i + 1}</span>
                            <h3>{name}</h3>
                            <p>{description}</p>
                          </div>
                        ))}
                      </div>
                      <div className="lab-position">
                        ↑ LAB ATUAL · ENTRE NÍVEIS 3 E 4
                      </div>
                      <p>
                        O LAB atual mede, interpreta e propõe melhorias. Ainda
                        não executa mudanças autônomas.
                      </p>
                      <p className="notice">
                        Learning Enterprise não significa auto-modificação sem
                        controle.
                        <br />
                        Self-learning is not uncontrolled self-modification.
                        <br />
                        Nível 5 não está operacional neste LAB.
                      </p>
                    </Panel>
                  </>
                )}
                {view === "settings" && (
                  <>
                    <Panel title="Configuração didática" tag="SOMENTE LEITURA">
                      <div className="kv">
                        <span>Versão</span>
                        <b>{data.settings.thresholds.version}</b>
                      </div>
                      <div className="kv">
                        <span>Janela padrão</span>
                        <b>{data.settings.thresholds.window_size} execuções</b>
                      </div>
                      <p>{data.settings.demo_profile}</p>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>SLO</th>
                              <th>Operador</th>
                              <th>Alvo</th>
                              <th>Severidade</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.settings.thresholds.slos.map((s) => (
                              <tr key={s.slo_id}>
                                <td>{s.slo_id}</td>
                                <td>{s.operator}</td>
                                <td>{num(s.target)}</td>
                                <td>{label(s.severity)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Panel>
                    <Panel title="Regras e limites">
                      {data.settings.decision_rules.map((rule) => (
                        <p key={rule}>{rule}</p>
                      ))}
                      <p>
                        Regras determinísticas no backend. Nenhuma edição,
                        transição ou troca de modelo é executada nesta tela.
                      </p>
                    </Panel>
                  </>
                )}
                {view === "reports" && (
                  <Panel
                    title="Resumo executivo da força de trabalho"
                    tag={source === "didactic" ? "DIDÁTICO" : "HISTÓRICO"}
                  >
                    <p>
                      Atualizado em {date(data.updated_at)}. Escopo: fonte
                      selecionada, sem misturar fixtures e histórico.
                    </p>
                    <div className="quality-cards">
                      <div>
                        <small>Agentes ativos</small>
                        <b>{data.overview.active_agents}</b>
                      </div>
                      <div>
                        <small>Fora da meta</small>
                        <b>{data.overview.goals.off_target}</b>
                      </div>
                      <div>
                        <small>Propostas pendentes</small>
                        <b>{data.overview.pending_recommendations}</b>
                      </div>
                      <div>
                        <small>Conhecimento validado</small>
                        <b>{data.knowledge.counts.approved}</b>
                      </div>
                    </div>
                    <h3>Desempenho e limites</h3>
                    {goals(data.agents)}
                    <h3>Valor sob gestão / exposição potencial</h3>
                    <p>
                      {money(data.business_exposure.exposure_brl)} ·{" "}
                      {label(source)}. Valor realizado: não validado.
                    </p>
                    <p>
                      Atenção requerida: {data.attention.count} agentes.
                      Recomendações abertas:{" "}
                      {data.overview.pending_recommendations}.
                    </p>
                    <h3>Economia</h3>
                    <p>
                      {num(data.overview.estimated_cost_usd, "USD")} ·{" "}
                      {data.overview.cost_window}. Valor realizado desconhecido.
                    </p>
                    <h3>Qualidade</h3>
                    <p>
                      {data.overview.degraded_executions} execuções degradadas
                      na população exibida. Não há score único.
                    </p>
                    <h3>Aprendizados recentes</h3>
                    {data.knowledge.items.slice(0, 5).map((k) => (
                      <p key={k.id}>
                        <b>{k.title}</b> · {label(k.validation_status)}
                      </p>
                    ))}
                  </Panel>
                )}
              </>
            )
          )}
          {busy === "execution" && (
            <div role="status" className="toast">
              <Loader2 className="spin" size={16} /> Consultando execução…
            </div>
          )}
          <footer className="page-footer">
            <span>L3 Control Plane · LAB NovaCore</span>
            <span>Observar → Medir → Interpretar → Recomendar → Aprender</span>
          </footer>
        </div>
      </main>
      {maestroOpen && (
        <aside className="maestro-drawer" aria-label="Painel global do Maestro">
          {maestroPanel}
        </aside>
      )}
      {decision && (
        <Modal onClose={() => setDecision(null)}>
          <button
            className="icon-button modal-close"
            aria-label="Fechar recomendação"
            onClick={() => setDecision(null)}
          >
            <X />
          </button>
          <div className="eyebrow">
            DECISÃO EXPLICÁVEL · {names[decision.agent_id]}
          </div>
          <Decision r={decision} />
          <Button
            onClick={() => {
              setMaestroOverride({
                context_type: "recommendation",
                recommendation_id: decision.recommendation_id,
                agent_id: decision.agent_id,
                source,
                route: "decisions",
              });
              setDecision(null);
              setMaestroOpen(true);
            }}
          >
            Perguntar ao Maestro sobre esta recomendação
          </Button>
        </Modal>
      )}
    </div>
  );
}
