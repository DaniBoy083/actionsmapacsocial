import "server-only";
import { NextRequest } from "next/server";
import { backendUrl } from "@/lib/backend";

export async function integrationProxy(
  request: NextRequest,
  resource: "health" | "acoes/resumos",
) {
  const authorization = request.headers.get("authorization") || "";
  const headers = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
  };
  if (!/^Bearer acm_[a-f0-9]{32}_[A-Za-z0-9_-]{43}$/.test(authorization)) {
    return Response.json(
      { detail: "Informe um token de integração válido." },
      {
        status: 401,
        headers: {
          ...headers,
          "WWW-Authenticate": 'Bearer realm="actions-map-integrations"',
        },
      },
    );
  }
  const parameters = request.nextUrl.searchParams;
  const allowed = resource === "health" ? [] : ["page", "exportacao_id"];
  if (
    parameters.size > 2 ||
    [...parameters.keys()].some(
      (key) => !allowed.includes(key) || parameters.getAll(key).length !== 1,
    )
  ) {
    return Response.json(
      { detail: "Parâmetros de consulta inválidos." },
      { status: 422, headers },
    );
  }
  try {
    const url = new URL(`${backendUrl()}/api/v1/integracoes/${resource}`);
    for (const [key, value] of parameters) {
      if (value.length > 36)
        return Response.json(
          { detail: "Parâmetros de consulta inválidos." },
          { status: 422, headers },
        );
      url.searchParams.set(key, value);
    }
    const upstream = await fetch(url, {
      headers: { Authorization: authorization, Accept: "application/json" },
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(30_000),
    });
    const responseHeaders = new Headers(headers);
    for (const name of ["content-type", "retry-after", "www-authenticate"]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "Integração temporariamente indisponível." },
      { status: 503, headers },
    );
  }
}
