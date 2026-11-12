"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Chip, Pagination } from "@mui/material";
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
import { BeneficiaryDialog } from "@/features/beneficiaries/beneficiary-dialog";
import { BeneficiarySheet } from "@/features/beneficiaries/beneficiary-sheet";
import { InstitutionalSummary } from "./institutional-summary";
import type { Institutional } from "./institutional";
import { ActionAssignments } from "@/features/staff/action-assignments";
import { ClinicalDialog } from "@/features/clinical/clinical-dialog";
import { DesignationDialog } from "@/features/clinical/designation-dialog";

export function ActionDetail({ id }: { id: string }) {
  const session = useSession();
  const client = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [personOpen, setPersonOpen] = useState(false);
  const [editingPerson, setEditingPerson] = useState<string | undefined>();
  const [sheet, setSheet] = useState<{
    id: string;
    secondCopy: boolean;
  } | null>(null);
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(1);
  const [clinicalPerson, setClinicalPerson] = useState<{
    id: string;
    nome: string;
  } | null>(null);
  const [designationPerson, setDesignationPerson] = useState<{
    id: string;
    nome: string;
  } | null>(null);
  const clinicalAccess = useQuery({
    queryKey: ["acesso-clinico", id],
    gcTime: 0,
    queryFn: async () =>
      (await api.get<{ permitido: boolean }>(`/acoes/${id}/acesso-clinico`))
        .data,
  });
  const [institutionalVersion, setInstitutionalVersion] = useState<
    number | null
  >(null);
  const historical = useQuery({
    queryKey: ["institucional", id, institutionalVersion],
    enabled: institutionalVersion !== null,
    queryFn: async () =>
      (
        await api.get<{ institucional: Institutional }>(
          `/acoes/${id}/institucional/versoes/${institutionalVersion}`,
        )
      ).data,
  });
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
        <h2>Identificação institucional</h2>
        <p className="muted">
          Dados cadastrados pela Administração/Tecnologia para toda a ação.
        </p>
        <InstitutionalSummary actionId={id} value={row.institucional} />
        {!!row.versoes_institucionais?.length && (
          <details>
            <summary>Consultar versões institucionais anteriores</summary>
            <div className="actions-row">
              {row.versoes_institucionais.map((version) => (
                <Button
                  key={version}
                  onClick={() => setInstitutionalVersion(version)}
                >
                  Revisão {version}
                </Button>
              ))}
            </div>
            {institutionalVersion !== null && historical.isPending && (
              <p role="status">Carregando versão…</p>
            )}
            {historical.isError && (
              <Alert severity="error">{errorMessage(historical.error)}</Alert>
            )}
            {historical.data && (
              <>
                <h3>Revisão {institutionalVersion}</h3>
                <InstitutionalSummary
                  actionId={id}
                  value={historical.data.institucional}
                />
              </>
            )}
          </details>
        )}
      </section>
      <ActionAssignments action={row} />
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
              setEditingPerson(undefined);
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
            <div
              className="table-scroll"
              role="region"
              aria-label="Beneficiários cadastrados"
              tabIndex={0}
            >
              <table className="data-table">
                <caption className="sr-only">
                  Beneficiários da ação e suas fichas privadas
                </caption>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Município de residência</th>
                    <th>Ficha e cadastro</th>
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
                      <td>
                        <div className="actions-row">
                          <Button
                            disabled={row.status === "arquivada"}
                            aria-label={`Designar atendimento de ${person.nome}`}
                            onClick={() => setDesignationPerson(person)}
                          >
                            Designar profissional
                          </Button>
                          {clinicalAccess.data?.permitido && (
                            <Button
                              aria-label={`Campos clínicos de ${person.nome}`}
                              onClick={() => setClinicalPerson(person)}
                            >
                              Campos clínicos
                            </Button>
                          )}
                          <Button
                            aria-label={`Ver ficha de ${person.nome}`}
                            onClick={() =>
                              setSheet({ id: person.id, secondCopy: false })
                            }
                          >
                            Ver ficha
                          </Button>
                          <Button
                            aria-label={`Editar cadastro de ${person.nome}`}
                            onClick={() => {
                              setEditingPerson(person.id);
                              setPersonOpen(true);
                            }}
                          >
                            Editar
                          </Button>
                          <Button
                            aria-label={`Emitir segunda via de ${person.nome}`}
                            onClick={() =>
                              setSheet({ id: person.id, secondCopy: true })
                            }
                          >
                            Segunda via
                          </Button>
                        </div>
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
      {clinicalPerson && (
        <ClinicalDialog
          actionId={id}
          personId={clinicalPerson.id}
          personName={clinicalPerson.nome}
          onClose={() => setClinicalPerson(null)}
        />
      )}
      {designationPerson && (
        <DesignationDialog
          actionId={id}
          personId={designationPerson.id}
          personName={designationPerson.nome}
          onClose={() => setDesignationPerson(null)}
        />
      )}
      {editing && (
        <ActionDialog action={row} onClose={() => setEditing(false)} />
      )}
      {personOpen && (
        <BeneficiaryDialog
          actionId={id}
          personId={editingPerson}
          municipalities={municipalities.data || []}
          locations={row.locais}
          onClose={() => setPersonOpen(false)}
          onSaved={refresh}
        />
      )}
      {sheet && (
        <BeneficiarySheet
          actionId={id}
          personId={sheet.id}
          secondCopy={sheet.secondCopy}
          onClose={() => setSheet(null)}
        />
      )}
    </>
  );
}
