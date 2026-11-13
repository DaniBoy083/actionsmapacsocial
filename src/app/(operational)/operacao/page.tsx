"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Pagination } from "@mui/material";
import { api, errorMessage } from "@/lib/api";

export default function MyActions() {
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["operational-actions", page],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<{ items: { id: string; nome: string }[]; total: number }>(
          "/operacao/acoes",
          { params: { pagina: page } },
        )
      ).data,
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Minhas ações</h1>
          <p>Escolha uma ação para acessar seu trabalho.</p>
        </div>
      </div>
      <section className="panel">
        {query.isPending ? (
          <p role="status">Carregando ações…</p>
        ) : query.isError ? (
          <Alert severity="error">{errorMessage(query.error)}</Alert>
        ) : (
          <>
            {!query.data.items.length && (
              <p>
                Nenhuma ação vinculada. Solicite uma atribuição à Administração.
              </p>
            )}
            <div className="operational-actions">
              {query.data.items.map((action) => (
                <article key={action.id}>
                  <h2>{action.nome}</h2>
                  <Button
                    component={Link}
                    href={`/operacao/${action.id}`}
                    variant="contained"
                  >
                    Abrir {action.nome}
                  </Button>
                </article>
              ))}
            </div>
            <Pagination
              page={page}
              count={Math.ceil(query.data.total / 20)}
              onChange={(_, next) => setPage(next)}
            />
          </>
        )}
      </section>
    </>
  );
}
