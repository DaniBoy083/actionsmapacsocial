"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Pagination,
  TextField,
} from "@mui/material";
import { api, dateLabel, errorMessage } from "@/lib/api";
import { StaffDialog } from "./staff-dialog";
import { StaffAccess } from "./staff-access";
import { staffCategories, type PageResult, type Staff } from "./types";

function StaffHistory({
  staff,
  onClose,
}: {
  staff: Staff;
  onClose: () => void;
}) {
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["profissionais", staff.id, "historico", page],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<
          PageResult<{ versao: number; dados: Staff; registrado_em: string }>
        >(`/profissionais/${staff.id}/historico`, { params: { pagina: page } })
      ).data,
  });
  return (
    <Dialog
      open
      fullWidth
      maxWidth="md"
      onClose={onClose}
      aria-labelledby="staff-history-title"
    >
      <DialogTitle id="staff-history-title">
        Histórico de {staff.nome}
      </DialogTitle>
      <DialogContent>
        {query.isPending ? (
          <p role="status">Carregando histórico…</p>
        ) : query.isError ? (
          <Alert severity="error">{errorMessage(query.error)}</Alert>
        ) : (
          <>
            {query.data.items.map((item) => (
              <article className="panel" key={item.versao}>
                <h3>
                  Revisão {item.versao} · {dateLabel(item.registrado_em)}
                </h3>
                <p>
                  {item.dados.nome} · {staffCategories[item.dados.categoria]} ·{" "}
                  {item.dados.ativo ? "Ativo" : "Inativo"}
                </p>
                <p>
                  Registro:{" "}
                  {[
                    item.dados.registro_conselho,
                    item.dados.registro_numero,
                    item.dados.registro_uf,
                  ]
                    .filter(Boolean)
                    .join(" / ") || "Não se aplica"}
                </p>
                <p>
                  Conferência:{" "}
                  {item.dados.habilitacao_validada
                    ? item.dados.habilitacao_referencia
                    : "Sem conferência registrada"}
                  . Divulgação:{" "}
                  {item.dados.divulgacao_autorizada
                    ? "Autorizada"
                    : "Sem autorização vigente"}
                  .
                </p>
              </article>
            ))}
            <Pagination
              count={Math.ceil(query.data.total / 20)}
              page={page}
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

export function StaffList() {
  const [filters, setFilters] = useState({ busca: "", ativo: "", pagina: 1 });
  const [editing, setEditing] = useState<Staff | "new" | null>(null);
  const [history, setHistory] = useState<Staff | null>(null);
  const [access, setAccess] = useState<Staff | null>(null);
  const context = useQuery({
    queryKey: ["auth-context"],
    queryFn: async () =>
      (await api.get<{ acesso_operacional: boolean }>("/auth/context")).data,
  });
  const query = useQuery({
    queryKey: ["profissionais", filters],
    gcTime: 0,
    placeholderData: keepPreviousData,
    queryFn: async () =>
      (
        await api.get<PageResult<Staff>>("/profissionais", {
          params: { ...filters, ativo: filters.ativo || undefined },
        })
      ).data,
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Profissionais</h1>
          <p>
            Cadastre profissionais e recepção para compor as equipes das ações.
          </p>
        </div>
        <Button variant="contained" onClick={() => setEditing("new")}>
          Cadastrar profissional
        </Button>
      </div>
      <section className="panel">
        <div className="form-two">
          <TextField
            label="Buscar profissional por nome"
            value={filters.busca}
            onChange={(event) =>
              setFilters({ ...filters, busca: event.target.value, pagina: 1 })
            }
            slotProps={{ htmlInput: { maxLength: 160 } }}
          />
          <TextField
            select
            label="Situação do profissional"
            value={filters.ativo}
            onChange={(event) =>
              setFilters({ ...filters, ativo: event.target.value, pagina: 1 })
            }
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="true">Ativos</MenuItem>
            <MenuItem value="false">Inativos</MenuItem>
          </TextField>
        </div>
      </section>
      <section className="panel">
        {query.isPending ? (
          <p role="status">Carregando profissionais…</p>
        ) : query.isError ? (
          <Alert severity="error">
            {errorMessage(query.error)}{" "}
            <Button onClick={() => query.refetch()}>Tentar novamente</Button>
          </Alert>
        ) : (
          <>
            {!query.data.items.length ? (
              <p>Nenhum profissional encontrado.</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <caption className="sr-only">
                    Cadastro administrativo de profissionais
                  </caption>
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Categoria e registro</th>
                      <th>Situação</th>
                      <th>Opções</th>
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.items.map((staff) => (
                      <tr key={staff.id}>
                        <td>{staff.nome}</td>
                        <td>
                          {staffCategories[staff.categoria]}
                          <small>
                            {[
                              staff.registro_conselho,
                              staff.registro_numero,
                              staff.registro_uf,
                            ]
                              .filter(Boolean)
                              .join(" / ")}
                          </small>
                        </td>
                        <td>
                          <Chip
                            size="small"
                            variant="outlined"
                            label={staff.ativo ? "Ativo" : "Inativo"}
                          />
                          <small>
                            {staff.categoria === "RECEPCAO"
                              ? "Recepção"
                              : staff.habilitacao_validada
                                ? "Conferência registrada"
                                : "Aguardando conferência"}
                          </small>
                        </td>
                        <td>
                          <div className="actions-row">
                            {context.data?.acesso_operacional && (
                              <Button
                                aria-label={`Gerenciar acesso de ${staff.nome}`}
                                onClick={() => setAccess(staff)}
                              >
                                Acesso
                              </Button>
                            )}
                            <Button
                              aria-label={`Editar profissional ${staff.nome}`}
                              onClick={() => setEditing(staff)}
                            >
                              Editar
                            </Button>
                            <Button
                              aria-label={`Histórico de ${staff.nome}`}
                              onClick={() => setHistory(staff)}
                            >
                              Histórico
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Pagination
              count={Math.ceil(query.data.total / 20)}
              page={filters.pagina}
              onChange={(_, pagina) => setFilters({ ...filters, pagina })}
            />
          </>
        )}
      </section>
      {editing && (
        <StaffDialog
          staff={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
        />
      )}
      {history && (
        <StaffHistory staff={history} onClose={() => setHistory(null)} />
      )}
      {access && <StaffAccess staff={access} onClose={() => setAccess(null)} />}
    </>
  );
}
