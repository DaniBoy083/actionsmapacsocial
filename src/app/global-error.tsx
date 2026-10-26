"use client";
export default function GlobalError({
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <html lang="pt-BR">
      <head>
        <title>Serviço indisponível | AC Actions Map</title>
      </head>
      <body
        style={{
          margin: 0,
          padding: 32,
          background: "#fff8f9",
          color: "#65111f",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <main
          style={{
            maxWidth: 560,
            margin: "12vh auto",
            padding: 32,
            background: "white",
            borderRadius: 20,
          }}
        >
          <p>AC SOCIAL | AC ACTIONS MAP</p>
          <h1>Serviço temporariamente indisponível</h1>
          <p>Recarregue a página ou procure a equipe de Tecnologia.</p>
          <button
            onClick={retry}
            style={{
              background: "#b80d27",
              color: "white",
              border: 0,
              padding: "14px 22px",
              borderRadius: 12,
              cursor: "pointer",
            }}
          >
            Tentar novamente
          </button>
          <p>
            <a href="/login">Voltar ao acesso institucional</a>
          </p>
        </main>
      </body>
    </html>
  );
}
