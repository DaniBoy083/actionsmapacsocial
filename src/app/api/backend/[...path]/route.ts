import { NextRequest } from "next/server";
import { backendUrl } from "@/lib/backend";
const permitted =
  /^(auth\/(login|me|logout)|localidades\/pb|indicadores|tecnologia\/saude|acoes(?:\/[a-zA-Z0-9-]+(?:\/(beneficiarios|revisar|aprovar|publicar))?)?|importacoes\/(preview|confirmar|[a-zA-Z0-9-]+\/paginas\/\d+))$/;
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const targetPath = path.join("/");
  if (!permitted.test(targetPath))
    return Response.json({ detail: "Rota não encontrada." }, { status: 404 });
  if (
    !["GET", "HEAD"].includes(request.method) &&
    request.headers.get("origin") !== request.nextUrl.origin
  )
    return Response.json({ detail: "Origem não autorizada." }, { status: 403 });
  const headers = new Headers();
  for (const name of ["cookie", "content-type", "x-csrf-token", "origin"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const url = new URL(`${backendUrl()}/api/v1/${targetPath}`);
    url.search = request.nextUrl.search;
    let body: string | undefined;
    if (!["GET", "HEAD"].includes(request.method) && request.body) {
      const reader = request.body.getReader();
      const chunks: Uint8Array[] = [];
      let bytes = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        bytes += value.byteLength;
        if (bytes > 1_048_576) {
          await reader.cancel();
          return Response.json(
            { detail: "Requisição muito grande." },
            { status: 413 },
          );
        }
        chunks.push(value);
      }
      body = Buffer.concat(chunks).toString("utf8");
    }
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(30_000),
    });
    const responseHeaders = new Headers({
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    for (const name of ["content-type", "retry-after"]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    for (const cookie of upstream.headers.getSetCookie())
      responseHeaders.append("set-cookie", cookie);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      {
        detail:
          "A API está indisponível. Confirme se o backend está em execução.",
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
export { proxy as GET, proxy as POST, proxy as PATCH, proxy as DELETE };
