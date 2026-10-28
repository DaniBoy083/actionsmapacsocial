"use client";
import { Controller, type UseFormReturn } from "react-hook-form";
import { MenuItem, TextField } from "@mui/material";
import type { Municipality, Location } from "@/lib/api";
import type { RegistrationForm } from "./registration";

export function RegistrationFields({
  form,
  municipalities,
  locations,
  nameLabel = "Nome",
  onChange,
}: {
  form: UseFormReturn<RegistrationForm>;
  municipalities: Municipality[];
  locations?: Location[];
  nameLabel?: string;
  onChange?: (values: RegistrationForm) => void;
}) {
  const {
    register,
    control,
    getValues,
    formState: { errors },
  } = form;
  const changed = () => onChange?.(getValues());
  const textFields = [
    ["nome", nameLabel, "text", 160],
    ["cpf", "CPF", "text", 14],
    ["cpf_documento", "CPF do documento (pendente de conferência)", "text", 14],
    ["telefone", "Telefone", "tel", 24],
    ["data_nascimento", "Data de nascimento", "date", undefined],
    ["data_ficha", "Data da ficha", "date", undefined],
    ["responsavel", "Responsável indicado na ficha", "text", 160],
    ["observacoes", "Observações gerais (sem dados oculares)", "text", 1000],
  ] as const;
  return (
    <>
      {textFields.map(([field, label, type, maxLength]) => (
        <TextField
          key={field}
          label={label}
          type={type}
          required={field === "nome"}
          autoComplete="off"
          multiline={field === "observacoes"}
          minRows={field === "observacoes" ? 3 : undefined}
          slotProps={{
            inputLabel: { shrink: type === "date" ? true : undefined },
            htmlInput: { maxLength },
          }}
          {...register(field, { onChange: changed })}
          error={!!errors[field]}
          helperText={errors[field]?.message}
        />
      ))}
      {(["municipio_ficha_ibge", "municipio_residencia_ibge"] as const).map(
        (name) => (
          <Controller
            key={name}
            name={name}
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                select
                label={
                  name === "municipio_ficha_ibge"
                    ? "Município indicado na ficha"
                    : "Município de residência (opcional)"
                }
                error={!!errors[name]}
                helperText={errors[name]?.message}
                onChange={(event) => {
                  field.onChange(event);
                  changed();
                }}
              >
                <MenuItem value="">Não informado / revisar</MenuItem>
                {municipalities.map((place) => (
                  <MenuItem key={place.codigo} value={place.codigo}>
                    {place.nome}
                  </MenuItem>
                ))}
              </TextField>
            )}
          />
        ),
      )}
      <Controller
        name="recebimento_confirmado"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            select
            label="Declaração de recebimento no documento"
            onChange={(event) => {
              field.onChange(event);
              changed();
            }}
          >
            <MenuItem value="">Não informado / revisar</MenuItem>
            <MenuItem value="sim">Recebimento confirmado</MenuItem>
            <MenuItem value="nao">Recebimento não confirmado</MenuItem>
          </TextField>
        )}
      />
      {locations && (
        <Controller
          name="local_indice"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              select
              label="Local da participação (opcional)"
              onChange={(event) => {
                field.onChange(event);
                changed();
              }}
            >
              <MenuItem value="">Não identificado / revisar</MenuItem>
              {locations.map((place, index) => (
                <MenuItem key={index} value={String(index)}>
                  {place.municipio_nome || place.municipio_ibge}
                  {place.nome_local ? ` · ${place.nome_local}` : ""}
                </MenuItem>
              ))}
            </TextField>
          )}
        />
      )}
    </>
  );
}
