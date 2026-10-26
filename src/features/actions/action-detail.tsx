"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
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
import toast from "react-hot-toast";
import {
  api,
  dateLabel,
  errorMessage,
  statusLabels,
  type Action,
  type Municipality,
} from "@/lib/api";
import { useSession } from "@/components/session-context";
import { ActionDialog } from "@/features/actions/action-dialog";

const personSchema = z.object({
  nome: z.string().trim().min(2, "Informe o nome.").max(160),
  municipio_residencia_ibge: z.string(),
  local_indice: z.string(),
});
export function ActionDetail({ id }: { id: string }) {
  const session = useSession();
  const client = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [personOpen, setPersonOpen] = useState(false);
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(1);
  const action = useQuery({
    queryKey: ["acoes", id],
    queryFn: async () => (await api.get<Action>(`/acoes/${id}`)).data,
    refetchInterval: (query) =>
      query.state.data?.status === "publicada" &&
      query.state.data.integracao?.status === "pendente"
        ? 5000
        : false,
  });
  const people = useQuery({
    queryKey: ["beneficiarios", id, page],
    queryFn: async () =>
      (
        await api.get<{
          items: {
            id: string;
            nome: string;
            municipio_residencia_ibge: string | null;
          }[];
          total: number;
        }>(`/acoes/${id}/beneficiarios`, { params: { pagina: page } })
      ).data,
  });
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof personSchema>>({
    resolver: zodResolver(personSchema),
    defaultValues: {
      nome: "",
      municipio_residencia_ibge: "",
      local_indice: "",
    },
  });
  async function addPerson(data: z.infer<typeof personSchema>) {
    setFailure("");
    try {
      await api.post(
        `/acoes/${id}/beneficiarios`,
        {
          ...data,
          municipio_residencia_ibge: data.municipio_residencia_ibge || null,
          local_indice: data.local_indice ? Number(data.local_indice) : null,
        },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      await refresh();
      setPersonOpen(false);
      reset();
      toast.success("Beneficiário registrado.");
    } catch (error) {
      setFailure(errorMessage(error));
    }
  }
  async function refresh() {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["acoes"] }),
      client.invalidateQueries({ queryKey: ["indicadores"] }),
      client.invalidateQueries({ queryKey: ["beneficiarios", id] }),
    ]);
  }
  async function transition(operation: string) {
    if (!action.data) return;
    setBusy(true);
    setFailure("");
    try {
      await api.post(
        `/acoes/${id}/${operation}`,
        { versao: action.data.versao },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      await refresh();
      toast.success("Status atualizado.");
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  if (action.isPending)
    return (
      <div className="panel" role="status">
        Carregando ação…
      </div>
    );
  if (action.isError)
    return (
      <Alert severity="error">
        {errorMessage(action.error)}{" "}
        <Button component={Link} href="/acoes">
          Voltar às ações
        </Button>
      </Alert>
    );
  const row = action.data;
  return (
    <>
      <div className="page-heading">
        <div>
          <Link href="/acoes" className="muted">
            ← Todas as ações
          </Link>
          <h1 style={{ marginTop: 12 }}>{row.nome}</h1>
          <Chip label={statusLabels[row.status]} variant="outlined" />
        </div>
        <div className="actions-row">
          <Button
            variant="outlined"
            onClick={() => setEditing(true)}
            disabled={row.status === "arquivada"}
          >
            Editar ação
          </Button>
          {row.status === "validada" && (
            <Button
              variant="contained"
              disabled={busy}
              onClick={() => transition("publicar")}
            >
              Publicar na Agenda
            </Button>
          )}
          {row.status === "em_revisao" && (
            <Button
              variant="contained"
              disabled={busy}
              onClick={() => transition("aprovar")}
            >
              Aprovar resumo
            </Button>
          )}
        </div>
      </div>
      {failure && !personOpen && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {failure}
        </Alert>
      )}
      <section className="panel">
        <h2>Informações da ação</h2>
        <div className="form-two">
          <div>
            <p className="muted">Categoria</p>
            <strong>{row.categoria || "Não informada"}</strong>
          </div>
          <div>
            <p className="muted">Período</p>
            <strong>
              {dateLabel(row.inicio_em)}
              {row.fim_em ? ` a ${dateLabel(row.fim_em)}` : ""}
            </strong>
          </div>
        </div>
        <p className="muted">Descrição interna</p>
        <p style={{ whiteSpace: "pre-wrap" }}>
          {row.descricao || "Sem descrição interna."}
        </p>
        <h2 style={{ marginTop: 28 }}>Locais de realização</h2>
        {row.locais.map((local, index) => (
          <p key={index}>
            <strong>{local.municipio_nome}</strong>
            {local.nome_local ? ` · ${local.nome_local}` : ""}
          </p>
        ))}
      </section>
      <section className="panel">
        <h2>Prévia do resumo público</h2>
        <p>
          <strong>{row.pessoas_contempladas ?? row.beneficiarios}</strong>{" "}
          pessoas contempladas · <strong>1</strong> ação ·{" "}
          {[...new Set(row.locais.map((place) => place.municipio_nome))].join(
            ", ",
          )}
        </p>
        <p style={{ whiteSpace: "pre-wrap" }}>
          {row.resumo_publico || "Resumo ainda não informado."}
        </p>
        <Alert severity="info">
          A Agenda recebe os totais da ação e os municípios, sem dados pessoais.
          O encaminhamento ao Portal depende do processamento na Plataforma.
        </Alert>
        {row.status === "publicada" && (
          <Alert
            severity={
              row.integracao?.status === "entregue" ? "success" : "info"
            }
            sx={{ mt: 2 }}
          >
            {row.integracao?.status === "entregue"
              ? "Recebimento confirmado pela Agenda Digital."
              : "Publicação registrada. Aguardando confirmação da Agenda Digital."}
          </Alert>
        )}
      </section>
      <section className="panel">
        <div className="page-heading">
          <div>
            <h2>Beneficiários da ação</h2>
            <p>Registros gerais, restritos a este módulo.</p>
          </div>
          <Button
            variant="contained"
            disabled={row.status === "arquivada"}
            onClick={() => {
              setPersonOpen(true);
              setFailure("");
            }}
          >
            Registrar beneficiário
          </Button>
        </div>
        {people.isPending ? (
          <p role="status">Carregando registros…</p>
        ) : people.isError ? (
          <Alert severity="error">{errorMessage(people.error)}</Alert>
        ) : !people.data.items.length ? (
          <p className="muted">Nenhum beneficiário registrado nesta ação.</p>
        ) : (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Município de residência</th>
                  </tr>
                </thead>
                <tbody>
                  {people.data.items.map((person) => (
                    <tr key={person.id}>
                      <td>{person.nome}</td>
                      <td>
                        {municipalities.data?.find(
                          (p) => p.codigo === person.municipio_residencia_ibge,
                        )?.nome || "Não identificado / revisar"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              sx={{ mt: 2 }}
              count={Math.ceil(people.data.total / 20)}
              page={page}
              onChange={(_, value) => setPage(value)}
            />
          </>
        )}
      </section>
      <section className="panel">
        <h2>Histórico de alterações</h2>
        {row.historico?.length ? (
          <ul>
            {row.historico.map((event, index) => (
              <li key={index} className="muted">
                {dateLabel(event.criado_em)} · {event.operacao}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Nenhuma alteração registrada.</p>
        )}
      </section>
      {editing && (
        <ActionDialog action={row} onClose={() => setEditing(false)} />
      )}
      <Dialog
        open={personOpen}
        onClose={() => {
          if (!isSubmitting) setPersonOpen(false);
        }}
        fullWidth
        maxWidth="sm"
        aria-labelledby="person-title"
      >
        <form onSubmit={handleSubmit(addPerson)} noValidate>
          <DialogTitle id="person-title">Registrar beneficiário</DialogTitle>
          <DialogContent>
            <p className="muted">
              Informe somente os dados gerais necessários. Município de
              residência pode ser diferente do local da ação.
            </p>
            {failure && <Alert severity="error">{failure}</Alert>}
            <div className="form-grid">
              <TextField
                label="Nome"
                autoFocus
                required
                {...register("nome")}
                error={!!errors.nome}
                helperText={errors.nome?.message}
              />
              <TextField
                select
                label="Município de residência (opcional)"
                defaultValue=""
                {...register("municipio_residencia_ibge")}
              >
                <MenuItem value="">Não identificado / revisar</MenuItem>
                {municipalities.data?.map((p) => (
                  <MenuItem key={p.codigo} value={p.codigo}>
                    {p.nome}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Local da participação (opcional)"
                defaultValue=""
                {...register("local_indice")}
              >
                <MenuItem value="">Não identificado / revisar</MenuItem>
                {row.locais.map((p, index) => (
                  <MenuItem key={index} value={String(index)}>
                    {p.municipio_nome}
                    {p.nome_local ? ` · ${p.nome_local}` : ""}
                  </MenuItem>
                ))}
              </TextField>
            </div>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              disabled={isSubmitting}
              onClick={() => setPersonOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="contained" disabled={isSubmitting}>
              {isSubmitting ? "Salvando…" : "Salvar beneficiário"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </>
  );
}
