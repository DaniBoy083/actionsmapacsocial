import { NextRequest } from "next/server";
import { backendUrl } from "@/lib/backend";
const privateHeaders = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};
const permitted =
  /^(auth\/(login|me|logout)|localidades\/pb|indicadores|profissionais(?:\/[a-f0-9-]{36}(?:\/historico)?)?|tecnologia\/(saude|sincronizar-agenda|tokens(?:\/[a-f0-9-]{36}\/(revogar|rotacionar))?)|acoes(?:\/[a-zA-Z0-9-]+(?:\/(beneficiarios(?:\/[a-zA-Z0-9-]+(?:\/segunda-via)?)?|atribuicoes(?:\/[a-f0-9-]{36}(?:\/historico)?)?|marcas\/[a-f0-9-]{36}|institucional\/versoes\/\d+|revisar|aprovar|publicar))?)?|importacoes\/(preview|confirmar|arquivos|[a-zA-Z0-9-]+(?:\/(preparar|paginas\/\d+|partes\/\d+))?))$/;
const clinicalPath =
  /^acoes\/[a-f0-9-]{36}\/(acesso-clinico|beneficiarios\/[a-f0-9-]{36}\/(clinica|designacao-clinica))$/;
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const targetPath = path.join("/");
  const institutionPath =
    /^instituicoes(?:\/[a-f0-9-]{36}\/marcas\/[a-f0-9-]{36})$/;
  if (
    !permitted.test(targetPath) &&
    targetPath !== "auth/context" &&
    !clinicalPath.test(targetPath) &&
    targetPath !== "instituicoes" &&
    !institutionPath.test(targetPath)
  )
    return Response.json(
      { detail: "Rota não encontrada." },
      { status: 404, headers: privateHeaders },
    );
  if (
    !["GET", "HEAD"].includes(request.method) &&
    request.headers.get("origin") !== request.nextUrl.origin
  )
    return Response.json(
      { detail: "Origem não autorizada." },
      { status: 403, headers: privateHeaders },
    );
  const headers = new Headers();
  for (const name of ["cookie", "content-type", "x-csrf-token", "origin"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const url = new URL(`${backendUrl()}/api/v1/${targetPath}`);
    url.search = request.nextUrl.search;
    let body: ArrayBuffer | undefined;
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
            { status: 413, headers: privateHeaders },
          );
        }
        chunks.push(value);
      }
      const binary = new Uint8Array(bytes);
      let offset = 0;
      for (const chunk of chunks) {
        binary.set(chunk, offset);
        offset += chunk.byteLength;
      }
      body = binary.buffer;
    }
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(30_000),
    });
    const responseHeaders = new Headers(privateHeaders);
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
      { status: 503, headers: privateHeaders },
    );
  }
}
export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};
