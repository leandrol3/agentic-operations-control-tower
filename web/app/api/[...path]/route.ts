import { NextRequest } from "next/server";
export const runtime = "nodejs";
// Transport only. No costs, goals, knowledge validation or decisions here.
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (!["cockpit", "knowledge", "maestro"].includes(path[0]))
    return Response.json({ detail: "Rota indisponível" }, { status: 404 });
  const origin = request.headers.get("origin");
  if (
    request.method === "POST" &&
    origin &&
    origin !== request.nextUrl.origin &&
    origin !== `http://${request.headers.get("host")}`
  )
    return Response.json({ detail: "Origem não permitida" }, { status: 403 });
  try {
    const response = await fetch(
      `${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
      {
        method: request.method,
        headers: { "Content-Type": "application/json" },
        body: request.method === "GET" ? undefined : await request.text(),
        cache: "no-store",
        signal: AbortSignal.timeout(90000),
      },
    );
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "Não foi possível conectar ao serviço. Verifique se a API está disponível.",
      },
      { status: 503 },
    );
  }
}
export const GET = proxy;
export const POST = proxy;
