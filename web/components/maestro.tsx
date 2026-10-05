"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "./ui";
import type { Plan, Source } from "../lib/types";
import { label, names } from "../lib/labels";
export type MaestroContext = {
  context_type:
    | "workforce"
    | "agent"
    | "execution"
    | "recommendation"
    | "knowledge"
    | "lifecycle"
    | "economics";
  agent_id?: string;
  execution_id?: string;
  recommendation_id?: string;
  knowledge_id?: string;
  source: Source;
  route: string;
  selected_filters?: Record<string, string>;
};
type Reply = { plan: Plan; session_id: string };
type Message = {
  role: "user" | "assistant" | "context";
  text: string;
  reply?: Reply;
};
export function useConversation(refresh: () => void) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const session = useRef<string | null>(null),
    lock = useRef(false);
  const previous = useRef(""),
    failed = useRef<{ question: string; context: MaestroContext } | null>(null);
  function updateContext(context: MaestroContext, title: string) {
    const signature = JSON.stringify(context);
    if (signature !== previous.current) {
      if (previous.current)
        setMessages((m) => [
          ...m,
          { role: "context", text: `Contexto alterado para ${title}.` },
        ]);
      previous.current = signature;
    }
  }
  async function ask(text: string, context: MaestroContext) {
    if (lock.current || text.trim().length < 3) return;
    lock.current = true;
    setBusy(true);
    setError("");
    if (!session.current)
      session.current = "session-" + crypto.randomUUID().replaceAll("-", "");
    const retrying =
      failed.current?.question === text &&
      JSON.stringify(failed.current.context) === JSON.stringify(context);
    if (!retrying) setMessages((m) => [...m, { role: "user", text }]);
    setQuestion("");
    try {
      const res = await fetch("/api/maestro/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          session_id: session.current,
          context,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "Serviço temporariamente indisponível.",
        );
      }
      const reply: Reply = await res.json();
      session.current = reply.session_id;
      setMessages((m) => [
        ...m,
        { role: "assistant", text: reply.plan.diagnosis, reply },
      ]);
      failed.current = null;
      refresh();
    } catch (e) {
      failed.current = { question: text, context };
      setError(e instanceof Error ? e.message : "Falha de conexão.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return {
    messages,
    question,
    setQuestion,
    busy,
    error,
    ask,
    updateContext,
    retry: () =>
      failed.current && ask(failed.current.question, failed.current.context),
  };
}
export function MaestroPanel({
  chat,
  context,
  title,
  lifecycle,
  attention,
  onClose,
  onKnowledge,
}: {
  chat: ReturnType<typeof useConversation>;
  context: MaestroContext;
  title: string;
  lifecycle?: string;
  attention?: string[];
  onClose?: () => void;
  onKnowledge: (id: string) => void;
}) {
  const end = useRef<HTMLDivElement>(null);
  const contextKey = JSON.stringify(context);
  useEffect(() => {
    chat.updateContext(context, title);
  }, [contextKey, title]); // stable semantic context, not render identity
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [chat.messages, chat.busy]);
  const root = useRef<HTMLElement>(null),
    composer = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (onClose) {
      const previous = document.activeElement as HTMLElement;
      composer.current?.focus();
      return () => previous?.focus();
    }
  }, [!!onClose]);
  return (
    <section
      ref={root}
      className="maestro-conversation"
      aria-label="Conversa com o Maestro"
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose?.();
      }}
    >
      <div className="maestro-heading">
        <div>
          <h2>Maestro</h2>
          <p>Chief of Staff da Workforce Agêntica</p>
        </div>
        {onClose && (
          <Button
            variant="outline"
            onClick={onClose}
            aria-label="Fechar Maestro"
          >
            ×
          </Button>
        )}
      </div>
      <p className="chat-intro">
        O Maestro interpreta os sinais do Control Plane, consulta o Segundo
        Cérebro e coordena propostas de melhoria da força de trabalho agêntica.
      </p>
      <div className="context-chips">
        {context.context_type !== "agent" && <span>{title}</span>}
        <span>Fonte: {label(context.source)}</span>
        {context.agent_id && (
          <span>Agente: {names[context.agent_id] || context.agent_id}</span>
        )}
        {lifecycle && <span>Lifecycle: {label(lifecycle)}</span>}
        {context.execution_id && (
          <span title={context.execution_id}>
            Execução: {context.execution_id.slice(0, 8)}
          </span>
        )}
      </div>
      {context.context_type === "workforce" && !!attention?.length && (
        <p>
          Agentes em atenção:{" "}
          {attention.map((id) => names[id] || id).join(", ")}
        </p>
      )}
      <div className="suggestions">
        {[
          "Quem precisa de atenção?",
          "Como posso melhorar o agente de Supply?",
          "O que aprendemos hoje?",
          "Quais recomendações estão pendentes?",
          "Quais agentes deveriam entrar em revisão?",
        ].map((q) => (
          <button
            key={q}
            disabled={chat.busy}
            onClick={() => chat.ask(q, context)}
          >
            {q} ↗
          </button>
        ))}
      </div>
      <div
        className="conversation-history"
        aria-live="polite"
        aria-relevant="additions"
      >
        {!chat.messages.length && (
          <p className="notice">
            Contexto pronto. Envie uma pergunta para iniciar a análise. Nenhuma
            chamada ocorre ao abrir este painel.
          </p>
        )}
        {chat.messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "context"
                ? "context-notice"
                : m.role === "user"
                  ? "user-message"
                  : "assistant-message"
            }
          >
            {m.role !== "assistant"
              ? m.text
              : m.reply && (
                  <>
                    <div className="eyebrow">
                      SÍNTESE COM FONTES ·{" "}
                      {m.reply.plan.generated_by === "mock-deterministic"
                        ? "MOCK OFFLINE"
                        : m.reply.plan.generated_by.replace(
                            "openai:",
                            "OpenAI · ",
                          )}
                    </div>
                    <h3>Diagnóstico</h3>
                    <p>{m.text}</p>
                    <details className="plan-details">
                      <summary>Hipótese, plano de melhoria e staffs</summary>
                      {m.reply.plan.hypothesis && (
                        <>
                          <h4>Hipótese a verificar</h4>
                          <p>{m.reply.plan.hypothesis}</p>
                        </>
                      )}
                      <h3>Recomendação / Plano de melhoria</h3>
                      <p>{m.reply.plan.objective}</p>
                      <ol className="steps">
                        {m.reply.plan.steps.map((s, j) => (
                          <li key={j}>{s}</li>
                        ))}
                      </ol>
                      <h4>Resultado esperado</h4>
                      <p>{m.reply.plan.expected_result}</p>
                      <h4>Staffs sugeridos</h4>
                      <p>
                        {m.reply.plan.staff_assignments
                          .map((s) => `${s.name} (${s.status})`)
                          .join(" · ")}
                      </p>
                      <h4>Riscos / Limitações</h4>
                      <p>{m.reply.plan.risk}</p>
                      {!!m.reply.plan.knowledge_ids.length && (
                        <>
                          <h4>Conhecimento relacionado</h4>
                          {m.reply.plan.knowledge_ids.map((id) => (
                            <button
                              className="text-link"
                              key={id}
                              onClick={() => onKnowledge(id)}
                            >
                              {id} ↗
                            </button>
                          ))}
                        </>
                      )}
                    </details>
                    <details>
                      <summary>
                        Fontes utilizadas ({m.reply.plan.evidence.length})
                      </summary>
                      {m.reply.plan.evidence.map((f) => (
                        <p key={f.id}>
                          <b>{f.source}</b> · {f.text}
                        </p>
                      ))}
                    </details>
                    {m.reply.plan.usage && (
                      <details>
                        <summary>Custo desta consulta ao Maestro</summary>
                        <p>
                          {m.reply.plan.usage.model} ·{" "}
                          {m.reply.plan.usage.input_tokens} tokens de entrada ·{" "}
                          {m.reply.plan.usage.output_tokens} de saída
                        </p>
                        <p>
                          {m.reply.plan.usage.estimated_cost
                            ? `${m.reply.plan.usage.estimated_cost} ${m.reply.plan.usage.currency} estimados`
                            : "Pricing não configurado; custo desconhecido"}
                          . Separado da economia do workflow; não é fatura.
                        </p>
                      </details>
                    )}
                    <p className="notice">
                      Plano proposto · Aprovação humana obrigatória.
                      Recomendação não é autorização.
                    </p>
                  </>
                )}
          </div>
        ))}
        {chat.busy && (
          <p role="status" className="notice">
            Maestro está analisando o Control Plane e consultando o Segundo
            Cérebro…
          </p>
        )}
        {chat.error && (
          <div role="alert" className="chat-error">
            <p>{chat.error}</p>
            <p>
              Não foi possível concluir esta análise. Os dados do Control Plane
              continuam disponíveis.
            </p>
            <Button disabled={chat.busy} onClick={chat.retry}>
              Tentar análise novamente
            </Button>
          </div>
        )}
        <div ref={end} />
      </div>
      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          chat.ask(chat.question, context);
        }}
      >
        <textarea
          ref={composer}
          aria-label="Pergunta ao Maestro"
          value={chat.question}
          onChange={(e) => chat.setQuestion(e.target.value)}
          maxLength={2000}
          placeholder="Pergunte sobre os sinais e próximos passos…"
        />
        <Button
          disabled={chat.busy || chat.question.trim().length < 3}
          type="submit"
        >
          Enviar ↗
        </Button>
      </form>
      <small>O modelo propõe. Código mede e valida. O humano autoriza.</small>
      <Button disabled>Executar plano · indisponível</Button>
    </section>
  );
}
