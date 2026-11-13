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
  MenuItem,
  Pagination,
  TextField,
} from "@mui/material";
import { api, errorMessage, type Location, type Municipality } from "@/lib/api";
import { useSession } from "@/components/session-context";
import { InstitutionalSummary } from "@/features/actions/institutional-summary";
import type { Institutional } from "@/features/actions/institutional";
import { BeneficiaryDialog } from "@/features/beneficiaries/beneficiary-dialog";
import { BeneficiarySheet } from "@/features/beneficiaries/beneficiary-sheet";
import { ClinicalDialog } from "./clinical-dialog";

type Person = { id: string; nome: string; local_indice: number | null };
type Eligible = { id: string; nome: string; locais_indices: number[] | null };
type Action = {
  id: string;
  nome: string;
  institucional: Institutional;
  locais: Location[];
};

function Designation({
  actionId,
  person,
  onClose,
  onSaved,
}: {
  actionId: string;
  person: Person;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const session = useSession();
  const endpoint = `/operacao/acoes/${actionId}/beneficiarios/${person.id}/designacao-clinica`;
  const current = useQuery({
    queryKey: ["operational-designation", actionId, person.id],
    gcTime: 0,
    retry: false,
    queryFn: async () =>
      (
        await api.get<{
          versao: number;
          profissional_id: string | null;
          ativo: boolean;
        }>(endpoint)
      ).data,
  });
  const eligible = useQuery({
    queryKey: ["operational-eligible", actionId],
    gcTime: 0,
    queryFn: async () =>
      (await api.get<Eligible[]>(`/operacao/acoes/${actionId}/profissionais`))
        .data,
  });
  const [choice, setChoice] = useState("");
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(active = true) {
    if (!current.data) return;
    setBusy(true);
    setFailure("");
    try {
      await api.put(
        endpoint,
        {
          profissional_id: active ? choice : current.data.profissional_id,
          versao: current.data.versao,
          ativo: active,
        },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      await onSaved();
      onClose();
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog
      open
      onClose={busy ? undefined : onClose}
      fullWidth
      maxWidth="sm"
      aria-labelledby="operational-designation-title"
    >
      <DialogTitle id="operational-designation-title">
        Encaminhar {person.nome}
      </DialogTitle>
      <DialogContent>
        <p>
          Selecione o profissional responsável por este atendimento. Registros
          já preenchidos conservam sua autoria.
        </p>
        {failure && <Alert severity="error">{failure}</Alert>}
        {(current.isError || eligible.isError) && (
          <Alert severity="error">
            Não foi possível consultar os profissionais autorizados.
          </Alert>
        )}
        {current.isPending || eligible.isPending ? (
          <p role="status">Carregando responsáveis…</p>
        ) : (
          <TextField
            select
            fullWidth
            label="Profissional responsável"
            value={choice}
            onChange={(event) => setChoice(event.target.value)}
            sx={{ mt: 1 }}
          >
            <MenuItem value="">Selecione</MenuItem>
            {eligible.data
              ?.filter(
                (staff) =>
                  staff.locais_indices === null ||
                  (person.local_indice !== null &&
                    staff.locais_indices.includes(person.local_indice)),
              )
              .map((staff) => (
                <MenuItem key={staff.id} value={staff.id}>
                  {staff.nome}
                </MenuItem>
              ))}
          </TextField>
        )}
      </DialogContent>
      <DialogActions>
        <Button disabled={busy} onClick={onClose}>
          Cancelar encaminhamento
        </Button>
        {current.data?.ativo && (
          <Button disabled={busy} onClick={() => save(false)}>
            Remover designação
          </Button>
        )}
        <Button
          variant="contained"
          disabled={busy || !choice || !current.data}
          onClick={() => save()}
        >
          Salvar encaminhamento
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function OperationalAction({ id }: { id: string }) {
  const session = useSession();
  const reception = session.categoria === "RECEPCAO";
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<string | "new" | null>(null);
  const [sheet, setSheet] = useState<{ id: string; second: boolean } | null>(
    null,
  );
  const [clinical, setClinical] = useState<Person | null>(null);
  const [designation, setDesignation] = useState<Person | null>(null);
  const action = useQuery({
    queryKey: ["operational-action", id],
    gcTime: 0,
    retry: false,
    queryFn: async () => (await api.get<Action>(`/operacao/acoes/${id}`)).data,
  });
  const people = useQuery({
    queryKey: ["operational-people", id, page],
    gcTime: 0,
    retry: false,
    queryFn: async () =>
      (
        await api.get<{ items: Person[]; total: number }>(
          `/operacao/acoes/${id}/beneficiarios`,
          { params: { pagina: page } },
        )
      ).data,
  });
  const municipalities = useQuery({
    queryKey: ["operational-municipalities"],
    gcTime: 0,
    queryFn: async () =>
      (await api.get<Municipality[]>("/operacao/localidades/pb")).data,
  });
  async function refresh() {
    await people.refetch();
  }
  if (action.isPending) return <p role="status">Carregando ação…</p>;
  if (action.isError)
    return <Alert severity="error">{errorMessage(action.error)}</Alert>;
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action.data.nome}</h1>
          <p>
            {reception
              ? "Recepção e encaminhamento dos atendimentos do seu local."
              : "Seus atendimentos designados para esta ação."}
          </p>
        </div>
        {reception && (
          <Button
            variant="contained"
            onClick={() => setEditing("new")}
            disabled={!municipalities.data}
          >
            Registrar beneficiário
          </Button>
        )}
      </div>
      <section className="panel">
        <h2>Identificação da ação</h2>
        <InstitutionalSummary
          actionId={id}
          value={action.data.institucional}
          operational
        />
      </section>
      <section className="panel">
        <h2>{reception ? "Cadastros da recepção" : "Meus atendimentos"}</h2>
        {people.isPending ? (
          <p role="status">Carregando atendimentos…</p>
        ) : people.isError ? (
          <Alert severity="error">{errorMessage(people.error)}</Alert>
        ) : (
          <>
            {!people.data.items.length && (
              <p>
                {reception
                  ? "Nenhum cadastro neste local."
                  : "Nenhum atendimento designado. Aguarde o encaminhamento da recepção."}
              </p>
            )}
            <div className="table-scroll">
              <table className="data-table">
                <caption className="sr-only">
                  Atendimentos permitidos para este profissional
                </caption>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Local</th>
                    <th>Atendimento</th>
                  </tr>
                </thead>
                <tbody>
                  {people.data.items.map((person) => (
                    <tr key={person.id}>
                      <td>{person.nome}</td>
                      <td>
                        {action.data.locais.find(
                          (place) => place.indice === person.local_indice,
                        )?.nome_local || "Não informado"}
                      </td>
                      <td>
                        <div className="actions-row">
                          <Button
                            aria-label={`Ver ficha de ${person.nome}`}
                            onClick={() =>
                              setSheet({ id: person.id, second: false })
                            }
                          >
                            Ver cadastro
                          </Button>
                          {reception ? (
                            <>
                              <Button
                                aria-label={`Editar cadastro de ${person.nome}`}
                                onClick={() => setEditing(person.id)}
                              >
                                Editar cadastro
                              </Button>
                              <Button
                                aria-label={`Encaminhar ${person.nome}`}
                                onClick={() => setDesignation(person)}
                              >
                                Encaminhar
                              </Button>
                            </>
                          ) : (
                            <Button
                              aria-label={`Campos clínicos de ${person.nome}`}
                              onClick={() => setClinical(person)}
                            >
                              Campos clínicos
                            </Button>
                          )}
                          <Button
                            aria-label={`Emitir segunda via de ${person.nome}`}
                            onClick={() =>
                              setSheet({ id: person.id, second: true })
                            }
                          >
                            Segunda via do cadastro
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={page}
              count={Math.ceil(people.data.total / 20)}
              onChange={(_, next) => setPage(next)}
            />
          </>
        )}
      </section>
      {editing && municipalities.data && (
        <BeneficiaryDialog
          actionId={id}
          personId={editing === "new" ? undefined : editing}
          municipalities={municipalities.data}
          locations={action.data.locais}
          operational
          onClose={() => setEditing(null)}
          onSaved={refresh}
        />
      )}
      {sheet && (
        <BeneficiarySheet
          actionId={id}
          personId={sheet.id}
          secondCopy={sheet.second}
          operational
          onClose={() => setSheet(null)}
        />
      )}
      {clinical && (
        <ClinicalDialog
          actionId={id}
          personId={clinical.id}
          personName={clinical.nome}
          operational
          onClose={() => setClinical(null)}
        />
      )}
      {designation && (
        <Designation
          actionId={id}
          person={designation}
          onClose={() => setDesignation(null)}
          onSaved={refresh}
        />
      )}
    </>
  );
}
