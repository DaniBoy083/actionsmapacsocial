"use client";

import { MenuItem, TextField } from "@mui/material";

export const emptyInstitutionalFilters = {
  instrumento: "",
  numero_instrumento: "",
  autor: "",
  orgao: "",
  clinica: "",
  apoio: "",
  contratante: "",
  apoiador: "",
};

export function InstitutionalFilters({
  value,
  onChange,
}: {
  value: typeof emptyInstitutionalFilters;
  onChange: (
    key: keyof typeof emptyInstitutionalFilters,
    value: string,
  ) => void;
}) {
  return (
    <div className="filter-extra">
      {(
        [
          ["instrumento", "Emenda/convênio"],
          ["numero_instrumento", "Número do instrumento"],
          ["autor", "Autor da emenda"],
          ["orgao", "Órgão governamental"],
          ["clinica", "Clínica parceira"],
          ["contratante", "Contratante"],
          ["apoiador", "Apoiador"],
        ] as const
      ).map(([key, label]) => (
        <TextField
          key={key}
          label={label}
          value={value[key]}
          slotProps={{
            htmlInput: { maxLength: key === "numero_instrumento" ? 80 : 160 },
          }}
          onChange={(event) => onChange(key, event.target.value)}
        />
      ))}
      <TextField
        select
        label="Apoio"
        value={value.apoio}
        onChange={(event) => onChange("apoio", event.target.value)}
      >
        <MenuItem value="">Todos</MenuItem>
        <MenuItem value="TOTAL">Total</MenuItem>
        <MenuItem value="PARCIAL">Parcial</MenuItem>
      </TextField>
    </div>
  );
}
