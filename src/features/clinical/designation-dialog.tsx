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
import { api } from "@/lib/api";
import { useSession } from "@/components/session-context";
import {
  staffError,
  type Assignment,
  type PageResult,
} from "@/features/staff/types";

export function DesignationDialog({
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
  const session = useSession();
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [page, setPage] = useState(1);
  const endpoint = `/acoes/${actionId}/beneficiarios/${personId}/designacao-clinica`;
  const current = useQuery({
    queryKey: ["designacao-clinica", actionId, personId],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<{
          versao: number;
          profissional_id: string | null;
          ativo: boolean;
        }>(endpoint)
      ).data,
  });
  const staff = useQuery({
    queryKey: ["atribuicoes", actionId, "designacao", page],
    gcTime: 0,
    queryFn: async () =>
      (
        await api.get<PageResult<Assignment>>(
          `/acoes/${actionId}/atribuicoes`,
          { params: { pagina: page, tamanho: 100 } },
        )
      ).data,
  });
  async function save(active: boolean) {
    if (!current.data) return;
    const id = active ? selected : current.data.profissional_id;
    if (!id) return;
    setBusy(true);
    setFailure("");
    try {
      await api.put(
        endpoint,
        { profissional_id: id, versao: current.data.versao, ativo: active },
        {
          headers: { "X-CSRF-Token": session.csrf_token },
        },
      );
      onClose();
    } catch (error) {
      setFailure(staffError(error));
    } finally {
      setBusy(false);
    }
  }
  const eligible = staff.data?.items.filter(
    (row) =>
      row.ativo &&
      row.papel === "PROFISSIONAL" &&
      row.profissional.ativo &&
      row.profissional.habilitacao_validada &&
      row.profissional.registro_clinico_autorizado &&
      row.profissional.identidade_institucional_id,
  );
  return (
    <Dialog
      open
      fullWidth
      maxWidth="sm"
      onClose={busy ? undefined : onClose}
      aria-labelledby="designation-title"
    >
      <DialogTitle id="designation-title">
        Designar atendimento — {personName}
      </DialogTitle>
      <DialogContent>
        <p>
          Selecione o profissional responsável por este atendimento. O vínculo
          com a ação e o local será conferido ao salvar. Fichas já iniciadas
          conservam a autoria.
        </p>
        {(failure || current.isError || staff.isError) && (
          <Alert severity="error">
            {failure || staffError(current.error || staff.error)}
          </Alert>
        )}
        {current.isPending || staff.isPending ? (
          <p role="status">Carregando designação…</p>
        ) : (
          <>
            <p>
              {current.data?.ativo
                ? "Há designação ativa para este atendimento."
                : "Atendimento sem designação ativa."}
            </p>
            <TextField
              fullWidth
              select
              label="Profissional responsável pelo atendimento"
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
            >
              <MenuItem value="">Selecione</MenuItem>
              {eligible?.map((row) => (
                <MenuItem key={row.id} value={row.profissional_id}>
                  {row.profissional.nome}
                </MenuItem>
              ))}
            </TextField>
            {!eligible?.length && (
              <p>
                Nenhum profissional autorizado nesta página. Confira as
                atribuições, a habilitação e o vínculo individual.
              </p>
            )}
            {staff.data && staff.data.total > 100 && (
              <Pagination
                count={Math.ceil(staff.data.total / 100)}
                page={page}
                onChange={(_, value) => setPage(value)}
              />
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button disabled={busy} onClick={onClose}>
          Fechar designação
        </Button>
        <Button
          disabled={busy || !current.data?.ativo}
          onClick={() => void save(false)}
        >
          Revogar designação
        </Button>
        <Button
          variant="contained"
          disabled={busy || !selected || !current.data}
          onClick={() => void save(true)}
        >
          {busy ? "Salvando…" : "Salvar designação"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
