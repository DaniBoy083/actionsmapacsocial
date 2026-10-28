"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Checkbox, FormControlLabel } from "@mui/material";
import type { Municipality } from "@/lib/api";
import { RegistrationFields } from "@/features/beneficiaries/registration-fields";
import {
  registrationSchema,
  registrationValues,
  registrationPayload,
  type BeneficiaryData,
  type RegistrationForm,
} from "@/features/beneficiaries/registration";

export type RecordRow = Pick<
  BeneficiaryData,
  "nome" | "municipio_residencia_ibge" | "local_indice"
> &
  Partial<BeneficiaryData> & { pagina: number; revisado: boolean };
export function RecordFields({
  row,
  municipalities,
  canReview,
  onChange,
}: {
  row: RecordRow;
  municipalities: Municipality[];
  canReview: boolean;
  onChange: (values: Partial<RecordRow>) => void;
}) {
  const form = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: registrationValues(row),
  });
  return (
    <form
      className="form-grid"
      aria-label="Revisar registro"
      onSubmit={form.handleSubmit((values) =>
        onChange({ ...registrationPayload(values), revisado: true }),
      )}
    >
      <RegistrationFields
        form={form}
        municipalities={municipalities}
        nameLabel="Nome conferido no documento"
        onChange={(values) => onChange(registrationPayload(values))}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={row.revisado}
            disabled={!canReview || row.nome.trim().length < 2}
            onChange={(event) => {
              if (!event.target.checked) onChange({ revisado: false });
              else
                void form.handleSubmit((values) =>
                  onChange({ ...registrationPayload(values), revisado: true }),
                )();
            }}
          />
        }
        label="Conferi os dados gerais da ficha e selecionei este registro para importar."
      />
      <Alert severity="info">
        Não adivinhe dados ilegíveis ou ausentes. Graus e dados oculares não
        devem ser transcritos. O município da ficha não define automaticamente a
        residência ou o local da ação.
      </Alert>
    </form>
  );
}
