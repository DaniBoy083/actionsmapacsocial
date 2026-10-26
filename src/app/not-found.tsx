import Link from "next/link";
export default function NotFound() {
  return (
    <main id="conteudo" className="error-scene">
      <section className="error-card">
        <div className="eyebrow">AC Actions Map</div>
        <div className="error-code">404</div>
        <h1>Página não encontrada</h1>
        <p className="muted">
          Este endereço não está disponível. Volte à visão geral para continuar.
        </p>
        <Link href="/dashboard">Voltar à visão geral →</Link>
      </section>
    </main>
  );
}
