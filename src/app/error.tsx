"use client";
import Link from "next/link";
import { Button } from "@mui/material";
export default function ErrorPage({
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <main id="conteudo" className="error-scene">
      <section className="error-card" role="alert">
        <div className="eyebrow">AC Actions Map</div>
        <div className="error-code">!</div>
        <h1>Não foi possível abrir esta página</h1>
        <p className="muted">
          Tente novamente. Se o problema continuar, procure a equipe de
          Tecnologia.
        </p>
        <Button variant="contained" onClick={retry}>
          Tentar novamente
        </Button>
        <p>
          <Link href="/dashboard">Voltar à visão geral</Link>
        </p>
      </section>
    </main>
  );
}
