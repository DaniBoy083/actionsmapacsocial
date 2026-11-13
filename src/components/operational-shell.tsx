"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Alert, Button } from "@mui/material";
import { api, errorMessage, type Session } from "@/lib/api";
import { SessionContext } from "./session-context";

export function OperationalShell({
  session,
  children,
}: {
  session: Session;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const queries = useQueryClient();
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  const category =
    session.categoria === "MEDICO"
      ? "Oftalmologista"
      : session.categoria === "OPTOMETRISTA"
        ? "Optometrista"
        : "Recepção";
  async function logout() {
    setBusy(true);
    try {
      await api.post(
        "/operacao/auth/logout",
        {},
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      queries.clear();
      router.replace("/acesso");
      router.refresh();
    } catch (error) {
      setFailure(errorMessage(error));
      setBusy(false);
    }
  }
  return (
    <SessionContext value={session}>
      <main id="conteudo" className="operational-area">
        <header className="operational-header">
          <div className="operational-brand">
            <Image
              src="/logo-ac-social.png"
              alt="AC Social"
              width={48}
              height={48}
              unoptimized
            />
            <div>
              <strong>AC Actions Map</strong>
              <div>
                {category} · {session.nome}
              </div>
            </div>
          </div>
          <nav aria-label="Navegação da equipe" className="operational-nav">
            <Button component={Link} href="/operacao">
              Minhas ações
            </Button>
            <Button onClick={logout} disabled={busy}>
              Sair
            </Button>
          </nav>
        </header>
        {session.demonstracao && (
          <aside className="demo-banner" aria-label="Modo de demonstração">
            <strong>Demonstração · dados fictícios</strong>
            <span>Use somente dados sintéticos. Alterações descartáveis.</span>
          </aside>
        )}
        {failure && <Alert severity="error">{failure}</Alert>}
        {children}
      </main>
    </SessionContext>
  );
}
