"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  TextField,
} from "@mui/material";
import { api, errorMessage } from "@/lib/api";
import { useSession } from "@/components/session-context";
import type { Staff } from "./types";

type Access = { usuario: string; ativo: boolean; versao: number };
function Editor({
  staff,
  data,
  onClose,
}: {
  staff: Staff;
  data: Access;
  onClose: () => void;
}) {
  const session = useSession();
  const [username, setUsername] = useState(data.usuario);
  const [active, setActive] = useState(data.versao ? data.ativo : true);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      await api.put(
        `/profissionais/${staff.id}/acesso`,
        {
          usuario: username,
          ativo: active,
          versao: data.versao,
          nova_senha: password || undefined,
          senha_institucional: confirmation,
        },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      onClose();
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save}>
      <DialogContent>
        <p>
          Este acesso é exclusivo do Actions Map. As permissões vêm do cadastro
          profissional, das atribuições e das designações; não do nome de
          usuário.
        </p>
        {staff.identidade_institucional_id && (
          <Alert severity="warning">
            Este cadastro já tem vínculo institucional. Revise a origem da
            identidade antes de criar uma conta local.
          </Alert>
        )}
        {failure && <Alert severity="error">{failure}</Alert>}
        <div className="form-grid">
          <TextField
            label="Usuário de acesso"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="off"
            slotProps={{
              htmlInput: {
                minLength: 3,
                maxLength: 80,
                pattern: "[a-z0-9][a-z0-9._-]+",
              },
            }}
            helperText="Use letras minúsculas, números, ponto, hífen ou sublinhado."
          />
          <TextField
            label={data.versao ? "Nova senha (opcional)" : "Senha inicial"}
            required={!data.versao}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            slotProps={{ htmlInput: { minLength: 12, maxLength: 128 } }}
            helperText="Mínimo de 12 caracteres. Uma redefinição encerra as sessões existentes."
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={active}
                onChange={(e) => setActive(e.target.checked)}
              />
            }
            label="Acesso ativo"
          />
          <TextField
            label="Sua senha institucional"
            required
            type="password"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            autoComplete="current-password"
          />
        </div>
      </DialogContent>
      <DialogActions>
        <Button disabled={busy} onClick={onClose}>
          Cancelar acesso
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={busy || !!staff.identidade_institucional_id}
        >
          {busy ? "Salvando…" : "Salvar acesso"}
        </Button>
      </DialogActions>
    </form>
  );
}
export function StaffAccess({
  staff,
  onClose,
}: {
  staff: Staff;
  onClose: () => void;
}) {
  const query = useQuery({
    queryKey: ["staff-access", staff.id],
    gcTime: 0,
    staleTime: 0,
    retry: false,
    queryFn: async () =>
      (await api.get<Access>(`/profissionais/${staff.id}/acesso`)).data,
  });
  return (
    <Dialog
      open
      fullWidth
      maxWidth="sm"
      onClose={onClose}
      aria-labelledby="staff-access-title"
    >
      <DialogTitle id="staff-access-title">Acesso de {staff.nome}</DialogTitle>
      {query.isPending ? (
        <DialogContent role="status">Carregando acesso…</DialogContent>
      ) : query.isError ? (
        <DialogContent>
          <Alert severity="error">{errorMessage(query.error)}</Alert>
          <Button onClick={onClose}>Fechar acesso</Button>
        </DialogContent>
      ) : (
        <Editor staff={staff} data={query.data} onClose={onClose} />
      )}
    </Dialog>
  );
}
