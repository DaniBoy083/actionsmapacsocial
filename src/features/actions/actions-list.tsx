"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
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
import {
  FiArrowRight,
  FiEdit2,
  FiFilePlus,
  FiMapPin,
  FiPlus,
  FiTrash2,
} from "react-icons/fi";
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

export function ActionsList() {
  const session = useSession();
  const client = useQueryClient();
  const [filters, setFilters] = useState({
    busca: "",
    municipio: "",
    status: "",
    categoria: "",
    inicio: "",
    fim: "",
    pagina: 1,
  });
  const [editing, setEditing] = useState<Action | "new" | null>(null);
  const [archiving, setArchiving] = useState<Action | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const query = useQuery({
    queryKey: ["acoes", filters],
    queryFn: async () =>
      (
        await api.get<{ items: Action[]; total: number }>("/acoes", {
          params: filters,
        })
      ).data,
  });
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  function filter(name: string, value: string) {
    setFilters((old) => ({ ...old, [name]: value, pagina: 1 }));
  }
  async function archive() {
    if (!archiving) return;
    setBusy(true);
    setFailure("");
    try {
      await api.delete(`/acoes/${archiving.id}`, {
        data: { versao: archiving.versao },
        headers: { "X-CSRF-Token": session.csrf_token },
      });
      await client.invalidateQueries({ queryKey: ["acoes"] });
      await client.invalidateQueries({ queryKey: ["indicadores"] });
      toast.success("Ação arquivada.");
      setArchiving(null);
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Ações institucionais</h1>
          <p>
            Organize iniciativas, locais e registros gerais de beneficiários.
          </p>
        </div>
        <div className="actions-row">
          <Button
            component={Link}
            href="/dados-iniciais"
            variant="outlined"
            startIcon={<FiFilePlus />}
          >
            Cadastrar dados iniciais
          </Button>
          <Button
            variant="contained"
            startIcon={<FiPlus />}
            onClick={() => setEditing("new")}
          >
            Cadastrar nova ação
          </Button>
        </div>
      </div>
      <section className="panel" aria-label="Filtrar ações">
        <div className="filter-grid">
          <TextField
            label="Buscar por nome"
            value={filters.busca}
            onChange={(e) => filter("busca", e.target.value)}
          />
          <TextField
            select
            label="Município"
            value={filters.municipio}
            onChange={(e) => filter("municipio", e.target.value)}
          >
            <MenuItem value="">Todos os municípios</MenuItem>
            {municipalities.data?.map((p) => (
              <MenuItem key={p.codigo} value={p.codigo}>
                {p.nome}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Status"
            value={filters.status}
            onChange={(e) => filter("status", e.target.value)}
          >
            <MenuItem value="">Todos os status</MenuItem>
            {Object.entries(statusLabels).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
        </div>
        <div className="filter-extra">
          <TextField
            label="Categoria"
            value={filters.categoria}
            onChange={(e) => filter("categoria", e.target.value)}
          />
          <TextField
            type="date"
            label="De"
            value={filters.inicio}
            onChange={(e) => filter("inicio", e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            type="date"
            label="Até"
            value={filters.fim}
            onChange={(e) => filter("fim", e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
        </div>
      </section>
      {query.isError ? (
        <Alert severity="error">
          {errorMessage(query.error)}{" "}
          <Button onClick={() => query.refetch()}>Tentar novamente</Button>
        </Alert>
      ) : query.isPending ? (
        <div className="panel" role="status">
          Carregando ações…
        </div>
      ) : (
        <section className="panel table-panel" aria-label="Lista de ações">
          {!query.data.items.length ? (
            <div className="empty-state">
              <FiMapPin />
              <h2>
                {query.data.total
                  ? "Nenhuma ação nesta página"
                  : "Nenhuma ação encontrada"}
              </h2>
              <p className="muted">
                Cadastre uma iniciativa ou ajuste os filtros para encontrar as
                ações da instituição.
              </p>
              <Button variant="contained" onClick={() => setEditing("new")}>
                Cadastrar nova ação
              </Button>
            </div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Nome da ação</th>
                    <th scope="col">Datas</th>
                    <th scope="col">Locais / municípios</th>
                    <th scope="col">Beneficiários</th>
                    <th scope="col">Status</th>
                    <th scope="col">Opções</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.items.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <strong>{row.nome}</strong>
                        <small>{row.categoria || "Sem categoria"}</small>
                      </td>
                      <td>
                        {dateLabel(row.inicio_em)}
                        {row.fim_em && (
                          <small>até {dateLabel(row.fim_em)}</small>
                        )}
                      </td>
                      <td>
                        {[
                          ...new Set(row.locais.map((p) => p.municipio_nome)),
                        ].join(", ")}
                        <small>
                          {row.locais.length}{" "}
                          {row.locais.length === 1 ? "local" : "locais"}
                        </small>
                      </td>
                      <td>{row.beneficiarios}</td>
                      <td>
                        <Chip
                          label={statusLabels[row.status]}
                          size="small"
                          variant="outlined"
                        />
                      </td>
                      <td>
                        <div className="actions-row">
                          <Button
                            component={Link}
                            href={`/acoes/${row.id}`}
                            aria-label={`Visualizar ${row.nome}`}
                            title="Visualizar"
                          >
                            <FiArrowRight />
                          </Button>
                          <Button
                            disabled={row.status === "arquivada"}
                            onClick={() => setEditing(row)}
                            aria-label={`Editar ${row.nome}`}
                            title="Editar"
                          >
                            <FiEdit2 />
                          </Button>
                          <Button
                            disabled={row.status === "arquivada"}
                            onClick={() => {
                              setArchiving(row);
                              setFailure("");
                            }}
                            aria-label={`Arquivar ${row.nome}`}
                            title="Arquivar"
                          >
                            <FiTrash2 />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="table-pagination">
            <span>
              {query.data.total}{" "}
              {query.data.total === 1 ? "ação encontrada" : "ações encontradas"}
            </span>
            <Pagination
              count={Math.max(1, Math.ceil(query.data.total / 10))}
              page={filters.pagina}
              onChange={(_, pagina) =>
                setFilters((old) => ({ ...old, pagina }))
              }
              getItemAriaLabel={(type, page) =>
                type === "page"
                  ? `Página ${page}`
                  : type === "next"
                    ? "Próxima página"
                    : "Página anterior"
              }
            />
          </div>
        </section>
      )}
      {editing && (
        <ActionDialog
          action={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
        />
      )}
      <Dialog
        open={!!archiving}
        onClose={() => {
          if (!busy) setArchiving(null);
        }}
        aria-labelledby="archive-title"
      >
        <DialogTitle id="archive-title">Arquivar ação?</DialogTitle>
        <DialogContent>
          <p>
            A ação <strong>{archiving?.nome}</strong> deixará os indicadores
            ativos. Os registros de beneficiários e o histórico serão
            preservados.
          </p>
          {failure && <Alert severity="error">{failure}</Alert>}
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button disabled={busy} onClick={() => setArchiving(null)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={archive} disabled={busy}>
            {busy ? "Arquivando…" : "Confirmar arquivamento"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
