// Somente importado por Server Components e Route Handlers.
export function backendUrl(): string {
  const binding =
    process.env.VERCEL === "1" ? process.env.ACTIONS_BACKEND_URL : undefined;
  const configured = binding || process.env.ACTIONS_API_URL;
  if (process.env.VERCEL === "1" && !configured)
    throw new Error("Backend não configurado.");
  const url = new URL(configured || "http://127.0.0.1:8000");
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (!binding &&
      (url.pathname !== "/" ||
        (url.protocol === "http:" && (!local || process.env.VERCEL === "1"))))
  ) {
    throw new Error("Backend não configurado corretamente.");
  }
  // O binding pode incluir um prefixo interno; não descartá-lo com new URL('/path', base).
  return url.href.replace(/\/$/, "");
}
