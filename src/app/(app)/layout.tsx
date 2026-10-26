import { Suspense } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import type { Session } from "@/lib/api";
import { backendUrl } from "@/lib/backend";
// A verificação da identidade sempre aguarda a sessão atual do servidor.
export const instant = false;
async function SessionGate({ children }: { children: React.ReactNode }) {
  const token = (await cookies()).get("ac_actions_session");
  if (!token) redirect("/login");
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/api/v1/auth/me`, {
      headers: { Cookie: `ac_actions_session=${token.value}` },
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
  } catch {
    return (
      <main id="conteudo" className="error-scene">
        <div className="error-card">
          <h1>API indisponível</h1>
          <p>Inicie o backend e recarregue esta página.</p>
          <a href="/login">Voltar ao acesso institucional</a>
        </div>
      </main>
    );
  }
  if (response.status === 401 || response.status === 403) redirect("/login");
  if (!response.ok) throw new Error("Serviço de autenticação indisponível.");
  const session: Session = await response.json();
  return <AppShell session={session}>{children}</AppShell>;
}
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <main id="conteudo" className="error-scene" aria-busy="true">
          Verificando acesso institucional…
        </main>
      }
    >
      <SessionGate>{children}</SessionGate>
    </Suspense>
  );
}
