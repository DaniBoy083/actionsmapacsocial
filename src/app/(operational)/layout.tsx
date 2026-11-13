import { Suspense } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { backendUrl } from "@/lib/backend";
import type { Session } from "@/lib/api";
import { OperationalShell } from "@/components/operational-shell";

export const instant = false;
async function Gate({ children }: { children: React.ReactNode }) {
  const name =
    process.env.ACTIONS_LOCAL_DEMO === "1"
      ? "ac_actions_demo_operational"
      : "ac_actions_operational";
  const token = (await cookies()).get(name);
  if (!token) redirect("/acesso");
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/api/v1/operacao/auth/me`, {
      headers: { Cookie: `${name}=${token.value}` },
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
  } catch {
    return (
      <main id="conteudo" className="error-scene">
        <div className="error-card">
          <h1>API indisponível</h1>
          <p>Recarregue a página após restabelecer a conexão.</p>
        </div>
      </main>
    );
  }
  if (
    response.status === 401 ||
    response.status === 403 ||
    response.status === 503
  )
    redirect("/acesso");
  if (!response.ok) throw new Error("Acesso operacional indisponível.");
  const session: Session = await response.json();
  return <OperationalShell session={session}>{children}</OperationalShell>;
}
export default function OperationalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense
      fallback={
        <main id="conteudo" className="error-scene" aria-busy="true">
          Verificando acesso…
        </main>
      }
    >
      <Gate>{children}</Gate>
    </Suspense>
  );
}
