"use client";

import { Checkbox, FormControlLabel, MenuItem, TextField } from "@mui/material";
import {
  emptyInstitutional,
  instrumentLabels,
  type Institutional,
} from "./institutional";
import { InstitutionLinks } from "./institution-links";

export function InstitutionalFields({
  value,
  onChange,
}: {
  value: Institutional;
  onChange: (value: Institutional) => void;
  actionId?: string;
}) {
  const instrument = value.instrumento;
  function changeInstrument(patch: Partial<Institutional["instrumento"]>) {
    onChange({ ...value, instrumento: { ...instrument, ...patch } });
  }
  return (
    <>
      <InstitutionLinks
        value={value.contratantes}
        onChange={(contratantes) => onChange({ ...value, contratantes })}
      />
      <InstitutionLinks
        value={value.apoiadores}
        supporter
        onChange={(apoiadores) => onChange({ ...value, apoiadores })}
      />
      <fieldset className="institutional-fields">
        <legend>Emenda ou convênio</legend>
        <p className="muted">
          Preencha uma vez por ação. Os atendimentos herdam esses dados. A marca
          AC Social é fixa; logos de terceiros são opcionais em todas as
          modalidades de apoio.
        </p>
        <TextField
          select
          fullWidth
          label="Tipo de instrumento"
          value={instrument.tipo}
          onChange={(event) =>
            changeInstrument(
              event.target.value === "NAO_INFORMADO"
                ? emptyInstitutional().instrumento
                : { tipo: event.target.value as typeof instrument.tipo },
            )
          }
        >
          {Object.entries(instrumentLabels).map(([key, label]) => (
            <MenuItem value={key} key={key}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Nome/título da emenda ou convênio"
          value={instrument.nome}
          disabled={instrument.tipo === "NAO_INFORMADO"}
          onChange={(event) => changeInstrument({ nome: event.target.value })}
          slotProps={{ htmlInput: { maxLength: 160 } }}
        />
        <div className="form-two">
          <TextField
            label="Número da emenda/convênio"
            value={instrument.numero}
            disabled={instrument.tipo === "NAO_INFORMADO"}
            onChange={(event) =>
              changeInstrument({ numero: event.target.value })
            }
            slotProps={{ htmlInput: { maxLength: 80 } }}
          />
          <TextField
            label="Autor da emenda (quando aplicável)"
            value={instrument.autor}
            disabled={instrument.tipo === "NAO_INFORMADO"}
            onChange={(event) =>
              changeInstrument({ autor: event.target.value })
            }
            slotProps={{ htmlInput: { maxLength: 160 } }}
          />
        </div>
        <FormControlLabel
          control={
            <Checkbox
              checked={instrument.divulgacao_autorizada}
              disabled={!instrument.nome || instrument.tipo === "NAO_INFORMADO"}
              onChange={(_, checked) =>
                changeInstrument({ divulgacao_autorizada: checked })
              }
            />
          }
          label="Divulgação dos dados do instrumento autorizada pela instituição"
        />
        {(value.governo.nome || value.clinica.nome || value.apoio) && (
          <p className="muted">
            As marcas e a modalidade do cadastro anterior permanecem no
            histórico e na impressão. Revise os novos papéis sem presumir que um
            parceiro era contratante.
          </p>
        )}
      </fieldset>
    </>
  );
}
