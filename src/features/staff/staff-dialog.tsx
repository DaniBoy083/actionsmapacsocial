"use client";

import { useState } from "react";
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
  TextField,
  useMediaQuery,
} from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSession } from "@/components/session-context";
import {
  staffCategories,
  staffError,
  staffPayload,
  states,
  type Staff,
  type StaffData,
} from "./types";

export function StaffDialog({
  staff,
  onClose,
}: {
  staff?: Staff;
  onClose: () => void;
}) {
  const session = useSession();
  const client = useQueryClient();
  const mobile = useMediaQuery("(max-width:639px)");
  const [data, setData] = useState(staffPayload(staff));
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const clinical = data.categoria !== "RECEPCAO";
  function change(patch: Partial<StaffData>) {
    setData((current) => ({ ...current, ...patch }));
    setDirty(true);
  }
  function close() {
    if (
      !busy &&
      (!dirty || window.confirm("Descartar as alterações não salvas?"))
    )
      onClose();
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      const payload = { ...data, versao: staff?.versao ?? 0 };
      const options = { headers: { "X-CSRF-Token": session.csrf_token } };
      if (staff)
        await api.patch(`/profissionais/${staff.id}`, payload, options);
      else await api.post("/profissionais", payload, options);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["profissionais"] }),
        client.invalidateQueries({ queryKey: ["atribuicoes"] }),
        client.invalidateQueries({ queryKey: ["acesso-clinico"] }),
      ]);
      onClose();
    } catch (error) {
      setFailure(staffError(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog
      open
      onClose={close}
      fullWidth
      maxWidth="md"
      fullScreen={mobile}
      aria-labelledby="staff-dialog-title"
    >
      <form onSubmit={submit}>
        <DialogTitle id="staff-dialog-title">
          {staff ? "Editar profissional" : "Cadastrar profissional"}
        </DialogTitle>
        <DialogContent>
          <div className="form-grid">
            {failure && <Alert severity="error">{failure}</Alert>}
            <TextField
              autoFocus
              required
              label="Nome do profissional"
              value={data.nome}
              onChange={(event) => change({ nome: event.target.value })}
              slotProps={{ htmlInput: { minLength: 2, maxLength: 160 } }}
            />
            <TextField
              select
              label="Categoria profissional"
              value={data.categoria}
              onChange={(event) => {
                const categoria = event.target.value as StaffData["categoria"];
                change({
                  categoria,
                  registro_conselho: categoria === "MEDICO" ? "CRM" : null,
                  registro_numero: null,
                  registro_uf: null,
                  rqe: null,
                  habilitacao_validada: false,
                  habilitacao_referencia: "",
                  divulgacao_autorizada: false,
                  divulgacao_referencia: "",
                  identidade_institucional_id: null,
                  registro_clinico_autorizado: false,
                  autorizacao_clinica_referencia: "",
                });
              }}
            >
              {Object.entries(staffCategories).map(([key, label]) => (
                <MenuItem key={key} value={key}>
                  {label}
                </MenuItem>
              ))}
            </TextField>
            {clinical && (
              <>
                <div className="form-two">
                  <TextField
                    label="Conselho/órgão de registro"
                    required
                    value={data.registro_conselho || ""}
                    disabled={data.categoria === "MEDICO"}
                    onChange={(event) =>
                      change({ registro_conselho: event.target.value || null })
                    }
                    slotProps={{ htmlInput: { maxLength: 40 } }}
                  />
                  <TextField
                    label="Número do registro"
                    required
                    value={data.registro_numero || ""}
                    onChange={(event) =>
                      change({ registro_numero: event.target.value || null })
                    }
                    slotProps={{ htmlInput: { maxLength: 40 } }}
                  />
                </div>
                <div className="form-two">
                  <TextField
                    select
                    label="UF do registro"
                    value={data.registro_uf || ""}
                    required
                    onChange={(event) =>
                      change({ registro_uf: event.target.value || null })
                    }
                  >
                    <MenuItem value="">Não informada</MenuItem>
                    {states.map((state) => (
                      <MenuItem value={state} key={state}>
                        {state}
                      </MenuItem>
                    ))}
                  </TextField>
                  {data.categoria === "MEDICO" && (
                    <TextField
                      label="RQE (quando aplicável)"
                      value={data.rqe || ""}
                      onChange={(event) =>
                        change({ rqe: event.target.value || null })
                      }
                      slotProps={{ htmlInput: { maxLength: 40 } }}
                    />
                  )}
                </div>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={data.habilitacao_validada}
                      onChange={(_, checked) =>
                        change({
                          habilitacao_validada: checked,
                          ...(!checked
                            ? {
                                divulgacao_autorizada: false,
                                registro_clinico_autorizado: false,
                              }
                            : {}),
                        })
                      }
                    />
                  }
                  label="Conferência da habilitação registrada"
                />
                <TextField
                  label="Referência da conferência de habilitação"
                  required={data.habilitacao_validada}
                  value={data.habilitacao_referencia}
                  onChange={(event) =>
                    change({ habilitacao_referencia: event.target.value })
                  }
                  helperText="Informe o registro aceito e a referência de conferência pela instituição. Optometrista não utiliza CRM. Não inclua dados de pacientes."
                  slotProps={{ htmlInput: { maxLength: 200 } }}
                />
              </>
            )}
            {clinical && (
              <>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={data.registro_clinico_autorizado}
                      disabled={!data.habilitacao_validada}
                      onChange={(_, checked) =>
                        change({ registro_clinico_autorizado: checked })
                      }
                    />
                  }
                  label="Registro de campos clínicos autorizado"
                />
                <TextField
                  label="Referência da autorização clínica"
                  required={data.registro_clinico_autorizado}
                  value={data.autorizacao_clinica_referencia}
                  onChange={(event) =>
                    change({
                      autorizacao_clinica_referencia: event.target.value,
                    })
                  }
                  helperText="Registre a autorização específica e o escopo definidos pelo responsável clínico."
                  slotProps={{ htmlInput: { maxLength: 200 } }}
                />
                {data.identidade_institucional_id &&
                data.identidade_institucional_id !== session.profissional_id ? (
                  <>
                    <p>Há vínculo com outra identidade institucional.</p>
                    <Button
                      onClick={() =>
                        change({ identidade_institucional_id: null })
                      }
                    >
                      Remover vínculo institucional
                    </Button>
                  </>
                ) : (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={
                          data.identidade_institucional_id ===
                          session.profissional_id
                        }
                        onChange={(_, checked) =>
                          change({
                            identidade_institucional_id: checked
                              ? session.profissional_id
                              : null,
                          })
                        }
                      />
                    }
                    label="Vincular este profissional à minha identidade institucional"
                  />
                )}
              </>
            )}
            <FormControlLabel
              control={
                <Checkbox
                  checked={data.ativo}
                  onChange={(_, checked) =>
                    change({
                      ativo: checked,
                      ...(!checked ? { divulgacao_autorizada: false } : {}),
                    })
                  }
                />
              }
              label="Cadastro ativo"
            />
            {staff && (
              <Alert severity="info">
                Inativar ou alterar categoria, registro ou conferência de
                habilitação revoga as atribuições ativas. A reativação do
                cadastro exige revisar e reativar as atribuições separadamente.
              </Alert>
            )}
            {data.categoria === "MEDICO" && (
              <>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={data.divulgacao_autorizada}
                      disabled={!data.ativo || !data.habilitacao_validada}
                      onChange={(_, checked) =>
                        change({ divulgacao_autorizada: checked })
                      }
                    />
                  }
                  label="Divulgação de nome e CRM/UF autorizada pela instituição"
                />
                <TextField
                  label="Referência da autorização de divulgação"
                  required={data.divulgacao_autorizada}
                  value={data.divulgacao_referencia}
                  onChange={(event) =>
                    change({ divulgacao_referencia: event.target.value })
                  }
                  slotProps={{ htmlInput: { maxLength: 200 } }}
                />
                <p className="muted">
                  A publicação depende da revisão no fluxo institucional.
                </p>
              </>
            )}
          </div>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={close} disabled={busy}>
            Cancelar
          </Button>
          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Salvando…" : "Salvar profissional"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
