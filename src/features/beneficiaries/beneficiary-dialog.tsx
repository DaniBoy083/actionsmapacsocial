"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import toast from "react-hot-toast";
import { useSession } from "@/components/session-context";
import { api, errorMessage, type Location, type Municipality } from "@/lib/api";
import {
  registrationSchema,
  registrationValues,
  registrationPayload,
  type BeneficiarySheet,
  type RegistrationForm,
} from "./registration";
import { RegistrationFields } from "./registration-fields";
import "./beneficiary-sheet.css";

type Props = {
  actionId: string;
  personId?: string;
  municipalities: Municipality[];
  locations: Location[];
  onClose: () => void;
  onSaved: () => Promise<void>;
};
function Editor({
  data,
  onSaving,
  ...props
}: Props & { data?: BeneficiarySheet; onSaving: (value: boolean) => void }) {
  const session = useSession();
  const [failure, setFailure] = useState("");
  const form = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: registrationValues(data),
  });
  const busy = form.formState.isSubmitting;
  async function save(values: RegistrationForm) {
    setFailure("");
    onSaving(true);
    try {
      const path = `/acoes/${props.actionId}/beneficiarios`;
      const config = { headers: { "X-CSRF-Token": session.csrf_token } };
      if (data)
        await api.patch(
          `${path}/${data.id}`,
          { ...registrationPayload(values), versao: data.versao },
          config,
        );
      else await api.post(path, registrationPayload(values), config);
      await props.onSaved();
      props.onClose();
      toast.success(data ? "Cadastro atualizado." : "Beneficiário registrado.");
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      onSaving(false);
    }
  }
  return (
    <form
      className="beneficiary-registration-form"
      onSubmit={form.handleSubmit(save)}
      noValidate
    >
      <DialogTitle id="person-title">
        {data ? "Editar cadastro do beneficiário" : "Registrar beneficiário"}
      </DialogTitle>
      <DialogContent>
        <p className="muted">
          Transcreva os dados gerais da ficha. Deixe em branco o que não estiver
          informado; não preencha graus ou dados oculares. O município da ficha
          e a residência podem ser diferentes do local da ação.
        </p>
        {failure && <Alert severity="error">{failure}</Alert>}
        <div className="form-grid">
          <RegistrationFields
            form={form}
            municipalities={props.municipalities}
            locations={props.locations}
          />
        </div>
      </DialogContent>
      <DialogActions sx={{ p: 3 }}>
        <Button disabled={busy} onClick={props.onClose}>
          Cancelar
        </Button>
        <Button type="submit" variant="contained" disabled={busy}>
          {busy ? "Salvando…" : "Salvar beneficiário"}
        </Button>
      </DialogActions>
    </form>
  );
}
export function BeneficiaryDialog(props: Props) {
  const [saving, setSaving] = useState(false);
  const query = useQuery({
    queryKey: ["beneficiary-editor", props.actionId, props.personId],
    queryFn: async ({ signal }) =>
      (
        await api.get<BeneficiarySheet>(
          `/acoes/${props.actionId}/beneficiarios/${props.personId}`,
          { signal },
        )
      ).data,
    enabled: !!props.personId,
    gcTime: 0,
    staleTime: 0,
    retry: false,
  });
  return (
    <Dialog
      open
      onClose={() => {
        if (!saving) props.onClose();
      }}
      fullWidth
      maxWidth="sm"
      aria-labelledby="person-title"
    >
      {props.personId && query.isPending ? (
        <>
          <DialogTitle id="person-title">
            Editar cadastro do beneficiário
          </DialogTitle>
          <DialogContent role="status">Carregando ficha…</DialogContent>
        </>
      ) : props.personId && query.isError ? (
        <>
          <DialogTitle id="person-title">Ficha indisponível</DialogTitle>
          <DialogContent>
            <Alert severity="error">{errorMessage(query.error)}</Alert>
            <Button onClick={props.onClose}>Fechar</Button>
          </DialogContent>
        </>
      ) : (
        <Editor
          {...props}
          data={props.personId ? query.data : undefined}
          onSaving={setSaving}
        />
      )}
    </Dialog>
  );
}
