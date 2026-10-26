"use client";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Checkbox,
  FormControlLabel,
  MenuItem,
  TextField,
} from "@mui/material";
import type { Municipality } from "@/lib/api";

export type RecordRow = {
  pagina: number;
  nome: string;
  municipio_residencia_ibge: string | null;
  local_indice: null;
  revisado: boolean;
};
const schema = z.object({
  nome: z
    .string()
    .trim()
    .min(2, "Confira o nome.")
    .max(160, "Use até 160 caracteres."),
  municipio: z
    .string()
    .regex(/^25\d{5}$/, "Selecione um município válido.")
    .or(z.literal("")),
});
type Fields = z.infer<typeof schema>;

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
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: row.nome,
      municipio: row.municipio_residencia_ibge || "",
    },
  });
  return (
    <form
      className="form-grid"
      aria-label="Revisar registro"
      onSubmit={handleSubmit(() => onChange({ revisado: true }))}
    >
      <TextField
        label="Nome conferido no documento"
        slotProps={{ htmlInput: { maxLength: 160 } }}
        {...register("nome", {
          onChange: (event) => onChange({ nome: event.target.value }),
        })}
        error={!!errors.nome}
        helperText={
          errors.nome?.message ||
          "Não expanda abreviações nem adivinhe nomes ilegíveis. Deixe o registro pendente."
        }
      />
      <Controller
        name="municipio"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            select
            label="Município de residência"
            error={!!errors.municipio}
            helperText={errors.municipio?.message}
            onChange={(event) => {
              field.onChange(event);
              onChange({
                municipio_residencia_ibge: event.target.value || null,
              });
            }}
          >
            <MenuItem value="">Não identificado / revisar</MenuItem>
            {municipalities.map((place) => (
              <MenuItem key={place.codigo} value={place.codigo}>
                {place.nome}
              </MenuItem>
            ))}
          </TextField>
        )}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={row.revisado}
            disabled={!canReview || row.nome.trim().length < 2}
            onChange={(event) => {
              if (!event.target.checked) onChange({ revisado: false });
              else void handleSubmit(() => onChange({ revisado: true }))();
            }}
          />
        }
        label="Conferi este nome e município e selecionei este registro para importar."
      />
      <Alert severity="info">
        O município de residência não define o local da ação. Registros não
        selecionados continuam pendentes.
      </Alert>
    </form>
  );
}
