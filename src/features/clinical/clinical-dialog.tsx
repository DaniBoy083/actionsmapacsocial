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
  TextField,
} from "@mui/material";
import { api } from "@/lib/api";
import { useSession } from "@/components/session-context";
import { InstitutionalSummary } from "@/features/actions/institutional-summary";
import type { Institutional } from "@/features/actions/institutional";
import { staffError } from "@/features/staff/types";

type Eye = {
  esferico: string | null;
  cilindrico: string | null;
  eixo: string | null;
  dp: string | null;
};
type Fields = {
  glicose: string | null;
  pressao: string | null;
  tipo_sangue: string | null;
  od: Eye;
  oe: Eye;
  adicao: string | null;
  lentes: string | null;
};
type ClinicalView = {
  id: string | null;
  versao: number;
  campos: Fields;
  contexto: {
    acao: { id: string; nome: string; versao: number };
    institucional: Institutional;
    profissional: {
      nome: string;
      registro_conselho: string | null;
      registro_numero: string | null;
      registro_uf: string | null;
    };
  };
};

function ClinicalEditor({
  data,
  endpoint,
  historical,
  onClose,
}: {
  data: ClinicalView;
  endpoint: string;
  historical: boolean;
  onClose: () => void;
}) {
  const session = useSession();
  const [fields, setFields] = useState(data.campos);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (historical) return;
    setBusy(true);
    setFailure("");
    try {
      await api.put(
        endpoint,
        { campos: fields, versao: data.versao },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      onClose();
    } catch (error) {
      setFailure(staffError(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save}>
      {failure && <Alert severity="error">{failure}</Alert>}
      <fieldset disabled={historical || busy} className="institutional-fields">
        <legend>
          Campos da ficha ·{" "}
          {data.versao ? `revisão ${data.versao}` : "novo registro"}
        </legend>
        <div className="form-two">
          {(
            [
              ["glicose", "Glicose", 80],
              ["pressao", "Pressão", 80],
              ["tipo_sangue", "Tipo de sangue", 32],
            ] as const
          ).map(([key, label, maxLength]) => (
            <TextField
              key={key}
              label={label}
              value={fields[key] || ""}
              onChange={(event) =>
                setFields({ ...fields, [key]: event.target.value || null })
              }
              slotProps={{ htmlInput: { maxLength } }}
            />
          ))}
        </div>
        <h3>Para longe</h3>
        {(["od", "oe"] as const).map((eye) => (
          <fieldset key={eye} className="institutional-fields">
            <legend>
              {eye === "od" ? "O.D. — olho direito" : "O.E. — olho esquerdo"}
            </legend>
            <div className="form-two">
              {(
                [
                  ["esferico", "Esférico"],
                  ["cilindrico", "Cilíndrico"],
                  ["eixo", "Eixo"],
                  ["dp", "DP"],
                ] as const
              ).map(([key, label]) => (
                <TextField
                  key={key}
                  label={`${label} ${eye.toUpperCase()}`}
                  value={fields[eye][key] || ""}
                  onChange={(event) =>
                    setFields({
                      ...fields,
                      [eye]: {
                        ...fields[eye],
                        [key]: event.target.value || null,
                      },
                    })
                  }
                  slotProps={{ htmlInput: { maxLength: 40 } }}
                />
              ))}
            </div>
          </fieldset>
        ))}
        <h3>Observações do quadro ocular</h3>
        <TextField
          label="Adição"
          value={fields.adicao || ""}
          onChange={(event) =>
            setFields({ ...fields, adicao: event.target.value || null })
          }
          slotProps={{ htmlInput: { maxLength: 40 } }}
        />
        <TextField
          label="Lentes"
          value={fields.lentes || ""}
          onChange={(event) =>
            setFields({ ...fields, lentes: event.target.value || null })
          }
          slotProps={{ htmlInput: { maxLength: 160 } }}
        />
      </fieldset>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>
          Fechar campos clínicos
        </Button>
        {!historical && (
          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Salvando…" : "Salvar campos clínicos"}
          </Button>
        )}
      </DialogActions>
    </form>
  );
}

export function ClinicalDialog({
  actionId,
  personId,
  personName,
  onClose,
}: {
  actionId: string;
  personId: string;
  personName: string;
  onClose: () => void;
}) {
  const [versionText, setVersionText] = useState("");
  const [version, setVersion] = useState<number | null>(null);
  const endpoint = `/acoes/${actionId}/beneficiarios/${personId}/clinica`;
  const query = useQuery({
    queryKey: ["campos-clinicos", actionId, personId, version],
    gcTime: 0,
    staleTime: 0,
    retry: false,
    queryFn: async ({ signal }) =>
      (
        await api.get<ClinicalView>(endpoint, {
          signal,
          params: version ? { versao: version } : {},
        })
      ).data,
  });
  return (
    <Dialog
      open
      fullWidth
      maxWidth="md"
      onClose={onClose}
      aria-labelledby="clinical-title"
    >
      <DialogTitle id="clinical-title">
        Campos clínicos — {personName}
      </DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mb: 2 }}>
          Registro em preenchimento. Transcreva os valores, sinais e unidades
          conforme informados pelo profissional. Campos sem informação podem
          ficar em branco. A conclusão do exame e os documentos dependem da
          validação do fluxo clínico.
        </Alert>
        <div className="actions-row">
          <TextField
            label="Número da versão para consulta"
            type="number"
            value={versionText}
            onChange={(event) => setVersionText(event.target.value)}
            slotProps={{ htmlInput: { min: 1, step: 1 } }}
          />
          <Button
            disabled={!/^[1-9]\d*$/.test(versionText)}
            onClick={() => setVersion(Number(versionText))}
          >
            Consultar versão
          </Button>
          <Button
            onClick={() => {
              setVersion(null);
              setVersionText("");
            }}
          >
            Versão atual
          </Button>
        </div>
        {query.isPending ? (
          <p role="status">Carregando campos clínicos…</p>
        ) : query.isError ? (
          <Alert severity="error">{staffError(query.error)}</Alert>
        ) : (
          <>
            <p>
              Ação: {query.data.contexto.acao.nome} · identificação
              institucional da revisão {query.data.contexto.acao.versao}.
            </p>
            <InstitutionalSummary
              actionId={actionId}
              value={query.data.contexto.institucional}
            />
            <p>
              Profissional do registro: {query.data.contexto.profissional.nome}{" "}
              ·{" "}
              {[
                query.data.contexto.profissional.registro_conselho,
                query.data.contexto.profissional.registro_numero,
                query.data.contexto.profissional.registro_uf,
              ]
                .filter(Boolean)
                .join(" / ")}
            </p>
            {version !== null && (
              <Alert severity="info">
                Consulta histórica, somente leitura.
              </Alert>
            )}
            <ClinicalEditor
              key={`${query.data.id}-${query.data.versao}-${version ?? "atual"}`}
              data={query.data}
              endpoint={endpoint}
              historical={version !== null}
              onClose={onClose}
            />
          </>
        )}
      </DialogContent>
      {(query.isError || query.isPending) && (
        <DialogActions>
          <Button onClick={onClose}>Fechar campos clínicos</Button>
        </DialogActions>
      )}
    </Dialog>
  );
}
