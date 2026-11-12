"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Pagination,
} from "@mui/material";
import { api, dateLabel } from "@/lib/api";
import { staffError, type Assignment, type PageResult } from "./types";

export function AssignmentHistory({
  assignment,
  onClose,
}: {
  assignment: Assignment;
  onClose: () => void;
}) {
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: [
      "atribuicoes",
      assignment.acao_id,
      assignment.id,
      "historico",
      page,
    ],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<
          PageResult<{
            versao: number;
            dados: Assignment;
            registrado_em: string;
          }>
        >(
          `/acoes/${assignment.acao_id}/atribuicoes/${assignment.id}/historico`,
          { params: { pagina: page } },
        )
      ).data,
  });
  return (
    <Dialog
      open
      fullWidth
      maxWidth="sm"
      onClose={onClose}
      aria-labelledby="assignment-history-title"
    >
      <DialogTitle id="assignment-history-title">
        Histórico da atribuição
      </DialogTitle>
      <DialogContent>
        {query.isPending ? (
          <p role="status">Carregando histórico…</p>
        ) : query.isError ? (
          <Alert severity="error">{staffError(query.error)}</Alert>
        ) : (
          <>
            {query.data.items.map((item) => (
              <article className="panel" key={item.versao}>
                <h3>
                  Revisão {item.versao} · {dateLabel(item.registrado_em)}
                </h3>
                <p>
                  {item.dados.profissional_snapshot.nome} ·{" "}
                  {item.dados.papel === "RECEPCAO"
                    ? "Recepção"
                    : "Profissional"}{" "}
                  · {item.dados.ativo ? "Ativa" : "Revogada"}
                </p>
                <p>
                  {item.dados.locais_snapshot
                    ? item.dados.locais_snapshot
                        .map(
                          (place) =>
                            `${place.indice + 1}: ${place.nome_local || place.municipio_ibge}`,
                        )
                        .join("; ")
                    : "Todos os locais da ação"}
                </p>
              </article>
            ))}
            <Pagination
              page={page}
              count={Math.ceil(query.data.total / 20)}
              onChange={(_, next) => setPage(next)}
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar histórico</Button>
      </DialogActions>
    </Dialog>
  );
}
