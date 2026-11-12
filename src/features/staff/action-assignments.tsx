"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Pagination,
  TextField,
} from "@mui/material";
import { api, type Action } from "@/lib/api";
import { useSession } from "@/components/session-context";
import { AssignmentHistory } from "./assignment-history";
import {
  staffCategories,
  staffError,
  type Assignment,
  type PageResult,
  type Staff,
} from "./types";

export function ActionAssignments({ action }: { action: Action }) {
  const client = useQueryClient();
  const session = useSession();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [opened, setOpened] = useState(false);
  const [editing, setEditing] = useState<Assignment | null>(null);
  const [selected, setSelected] = useState<Staff | null>(null);
  const [allLocations, setAllLocations] = useState(true);
  const [indices, setIndices] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [history, setHistory] = useState<Assignment | null>(null);
  const assignments = useQuery({
    queryKey: ["atribuicoes", action.id, page],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<PageResult<Assignment>>(
          `/acoes/${action.id}/atribuicoes`,
          { params: { pagina: page } },
        )
      ).data,
  });
  const candidates = useQuery({
    queryKey: ["profissionais", "candidatos", search],
    enabled: opened,
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<PageResult<Staff>>("/profissionais", {
          params: { ativo: true, busca: search },
        })
      ).data,
  });
  async function refresh() {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["atribuicoes", action.id] }),
      client.invalidateQueries({ queryKey: ["acoes", action.id] }),
      client.invalidateQueries({ queryKey: ["acesso-clinico", action.id] }),
    ]);
  }
  function open(row?: Assignment) {
    setEditing(row ?? null);
    setSelected(row?.profissional ?? null);
    setSearch("");
    setAllLocations(row?.locais_indices == null);
    setIndices(row?.locais_indices ?? []);
    setFailure("");
    setOpened(true);
  }
  async function persist(row?: Assignment) {
    const member = row?.profissional ?? selected;
    if (!member) return;
    setBusy(true);
    setFailure("");
    const payload = {
      acao_versao: action.versao,
      profissional_versao: member.versao,
      locais_indices: row ? row.locais_indices : allLocations ? null : indices,
    };
    try {
      const options = { headers: { "X-CSRF-Token": session.csrf_token } };
      if (row || editing) {
        const current = row ?? editing!;
        await api.patch(
          `/acoes/${action.id}/atribuicoes/${current.id}`,
          { ...payload, ativo: !row, versao: current.versao },
          options,
        );
      } else
        await api.post(
          `/acoes/${action.id}/atribuicoes`,
          { ...payload, profissional_id: member.id },
          options,
        );
      await refresh();
      setOpened(false);
    } catch (error) {
      setFailure(staffError(error));
    } finally {
      setBusy(false);
    }
  }
  const options = candidates.data?.items ?? [];
  const members =
    selected && !options.some((row) => row.id === selected.id)
      ? [selected, ...options]
      : options;
  const eligible =
    selected?.ativo &&
    (selected.categoria === "RECEPCAO" || selected.habilitacao_validada);
  return (
    <section className="panel">
      <div className="page-heading">
        <div>
          <h2>Equipe da ação</h2>
          <p>
            Profissionais escalados e locais de atuação. O acesso operacional é
            liberado em etapa própria.
          </p>
        </div>
        <div className="actions-row">
          <Button component={Link} href="/profissionais">
            Gerenciar profissionais
          </Button>
          <Button
            variant="outlined"
            disabled={action.status === "arquivada"}
            onClick={() => open()}
          >
            Atribuir profissional
          </Button>
        </div>
      </div>
      {failure && !opened && (
        <Alert severity="error">
          {failure} <Button onClick={refresh}>Recarregar dados</Button>
        </Alert>
      )}
      {assignments.isPending ? (
        <p role="status">Carregando equipe…</p>
      ) : assignments.isError ? (
        <Alert severity="error">{staffError(assignments.error)}</Alert>
      ) : (
        <>
          {!assignments.data.items.length ? (
            <p>Nenhum profissional atribuído.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <caption className="sr-only">
                  Profissionais e escopo de locais da ação
                </caption>
                <thead>
                  <tr>
                    <th>Profissional</th>
                    <th>Escopo</th>
                    <th>Situação</th>
                    <th>Opções</th>
                  </tr>
                </thead>
                <tbody>
                  {assignments.data.items.map((row) => (
                    <tr key={row.id}>
                      <td>
                        {row.profissional.nome}
                        <small>
                          {staffCategories[row.profissional.categoria]}
                        </small>
                        {row.profissional_snapshot.nome !==
                          row.profissional.nome && (
                          <small>
                            Nome no registro da atribuição:{" "}
                            {row.profissional_snapshot.nome}
                          </small>
                        )}
                      </td>
                      <td>
                        {row.locais_snapshot
                          ? row.locais_snapshot
                              .map(
                                (place) =>
                                  `${place.indice + 1}: ${place.nome_local || place.municipio_ibge}`,
                              )
                              .join("; ")
                          : "Todos os locais da ação"}
                      </td>
                      <td>{row.ativo ? "Ativa" : "Revogada"}</td>
                      <td>
                        <div className="actions-row">
                          <Button
                            aria-label={`Revisar atribuição de ${row.profissional.nome}`}
                            disabled={busy || action.status === "arquivada"}
                            onClick={() => open(row)}
                          >
                            {row.ativo ? "Revisar locais" : "Reativar"}
                          </Button>
                          <Button
                            aria-label={`Histórico da atribuição de ${row.profissional.nome}`}
                            onClick={() => setHistory(row)}
                          >
                            Histórico
                          </Button>
                          {row.ativo && (
                            <Button
                              aria-label={`Revogar atribuição de ${row.profissional.nome}`}
                              disabled={busy}
                              onClick={() => persist(row)}
                            >
                              Revogar
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Pagination
            page={page}
            count={Math.ceil(assignments.data.total / 20)}
            onChange={(_, next) => setPage(next)}
          />
        </>
      )}
      {history && (
        <AssignmentHistory
          assignment={history}
          onClose={() => setHistory(null)}
        />
      )}
      {opened && (
        <Dialog
          open
          fullWidth
          maxWidth="sm"
          onClose={() => {
            if (!busy) setOpened(false);
          }}
          aria-labelledby="assignment-title"
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void persist();
            }}
          >
            <DialogTitle id="assignment-title">
              {editing ? "Revisar atribuição" : "Atribuir profissional à ação"}
            </DialogTitle>
            <DialogContent>
              <div className="form-grid">
                {failure && (
                  <Alert severity="error">
                    {failure}{" "}
                    <Button onClick={refresh}>Recarregar dados</Button>
                  </Alert>
                )}
                {!editing && (
                  <TextField
                    label="Buscar profissional para atribuir"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    slotProps={{ htmlInput: { maxLength: 160 } }}
                  />
                )}
                <TextField
                  select
                  label="Profissional da equipe"
                  required
                  disabled={!!editing}
                  value={selected?.id || ""}
                  onChange={(event) =>
                    setSelected(
                      members.find((row) => row.id === event.target.value) ??
                        null,
                    )
                  }
                >
                  <MenuItem value="">Selecione</MenuItem>
                  {members.map((member) => (
                    <MenuItem
                      value={member.id}
                      key={member.id}
                      disabled={
                        !member.ativo ||
                        (member.categoria !== "RECEPCAO" &&
                          !member.habilitacao_validada)
                      }
                    >
                      {member.nome} · {staffCategories[member.categoria]}
                      {member.registro_numero
                        ? ` · ${member.registro_conselho}/${member.registro_uf} ${member.registro_numero}`
                        : ""}
                    </MenuItem>
                  ))}
                </TextField>
                {candidates.isError && (
                  <Alert severity="error">{staffError(candidates.error)}</Alert>
                )}
                {!eligible && selected && (
                  <Alert severity="warning">
                    Revise a situação e a conferência de habilitação no cadastro
                    do profissional antes de atribuí-lo.
                  </Alert>
                )}
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={allLocations}
                      onChange={(_, checked) => setAllLocations(checked)}
                    />
                  }
                  label="Todos os locais da ação"
                />
                {!allLocations &&
                  action.locais.map((place, index) => (
                    <FormControlLabel
                      key={index}
                      control={
                        <Checkbox
                          checked={indices.includes(index)}
                          onChange={(_, checked) =>
                            setIndices((current) =>
                              checked
                                ? [...current, index]
                                : current.filter((value) => value !== index),
                            )
                          }
                        />
                      }
                      label={`Local ${index + 1}: ${place.nome_local || place.municipio_nome}`}
                    />
                  ))}
                {editing?.locais_snapshot && (
                  <p className="muted">
                    Locais no registro anterior:{" "}
                    {editing.locais_snapshot
                      .map((place) => place.nome_local || place.municipio_ibge)
                      .join("; ")}
                    . Confira os locais atuais antes de salvar.
                  </p>
                )}
              </div>
            </DialogContent>
            <DialogActions sx={{ p: 3 }}>
              <Button onClick={() => setOpened(false)} disabled={busy}>
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={
                  busy || !eligible || (!allLocations && !indices.length)
                }
              >
                Salvar atribuição
              </Button>
            </DialogActions>
          </form>
        </Dialog>
      )}
    </section>
  );
}
