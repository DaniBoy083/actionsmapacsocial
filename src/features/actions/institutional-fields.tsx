"use client";

import { useState } from "react";
import Image from "next/image";
import {
  Alert,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  TextField,
} from "@mui/material";
import {
  emptyInstitutional,
  instrumentLabels,
  type Institutional,
} from "./institutional";

export function InstitutionalFields({
  value,
  onChange,
  actionId,
}: {
  value: Institutional;
  onChange: (value: Institutional) => void;
  actionId?: string;
}) {
  const [failure, setFailure] = useState("");
  const instrument = value.instrumento;
  function changeInstrument(patch: Partial<Institutional["instrumento"]>) {
    onChange({ ...value, instrumento: { ...instrument, ...patch } });
  }
  function changeBrand(
    slot: "governo" | "clinica",
    patch: Partial<Institutional["governo"]>,
  ) {
    onChange({ ...value, [slot]: { ...value[slot], ...patch } });
  }
  async function upload(slot: "governo" | "clinica", file?: File) {
    setFailure("");
    if (!file) return;
    if (
      file.size > 262144 ||
      !["image/png", "image/jpeg"].includes(file.type)
    ) {
      setFailure(
        "Use PNG/JPEG estático de 64 a 2048 pixels por lado e até 256 KiB.",
      );
      return;
    }
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const encoded = btoa(
        Array.from(bytes, (byte) => String.fromCharCode(byte)).join(""),
      );
      changeBrand(slot, { logo_id: null, conteudo_base64: encoded });
    } catch {
      setFailure(
        "Não foi possível ler a imagem. Selecione o arquivo novamente.",
      );
    }
  }
  return (
    <fieldset className="institutional-fields">
      <legend>Identificação institucional da ação</legend>
      <p className="muted">
        Preencha uma vez por ação. A marca AC Social é fixa; órgão e clínica são
        opcionais em qualquer modalidade de apoio.
      </p>
      <TextField
        select
        fullWidth
        label="Modalidade de apoio"
        value={value.apoio || ""}
        onChange={(event) =>
          onChange({
            ...value,
            apoio: (event.target.value || null) as Institutional["apoio"],
          })
        }
      >
        <MenuItem value="">Não informada</MenuItem>
        <MenuItem value="TOTAL">Total</MenuItem>
        <MenuItem value="PARCIAL">Parcial</MenuItem>
      </TextField>
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
          onChange={(event) => changeInstrument({ numero: event.target.value })}
          slotProps={{ htmlInput: { maxLength: 80 } }}
        />
        <TextField
          label="Autor da emenda (quando aplicável)"
          value={instrument.autor}
          disabled={instrument.tipo === "NAO_INFORMADO"}
          onChange={(event) => changeInstrument({ autor: event.target.value })}
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
      {(["governo", "clinica"] as const).map((slot) => {
        const brand = value[slot];
        const label =
          slot === "governo" ? "Órgão governamental" : "Clínica parceira";
        const source = brand.conteudo_base64
          ? `data:image/png;base64,${brand.conteudo_base64}`
          : brand.logo_id && actionId
            ? `/api/backend/acoes/${actionId}/marcas/${brand.logo_id}`
            : null;
        return (
          <fieldset className="institutional-fields" key={slot}>
            <legend>{label} (opcional)</legend>
            <TextField
              fullWidth
              label={`Nome: ${label.toLowerCase()}`}
              value={brand.nome}
              onChange={(event) =>
                changeBrand(slot, { nome: event.target.value })
              }
              slotProps={{ htmlInput: { maxLength: 160 } }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={brand.uso_autorizado}
                  onChange={(_, checked) =>
                    changeBrand(
                      slot,
                      checked
                        ? { uso_autorizado: true }
                        : {
                            uso_autorizado: false,
                            divulgacao_autorizada: false,
                            logo_id: null,
                            conteudo_base64: null,
                          },
                    )
                  }
                />
              }
              label={`Uso da marca de ${label.toLowerCase()} autorizado`}
            />
            <label className="logo-upload">
              Logo de {label.toLowerCase()}
              <input
                type="file"
                accept="image/png,image/jpeg"
                disabled={!brand.nome || !brand.uso_autorizado}
                onChange={(event) => {
                  void upload(slot, event.target.files?.[0]);
                  event.target.value = "";
                }}
              />
            </label>
            <p className="muted">
              PNG ou JPEG estático, 64 a 2048 pixels por lado, até 256 KiB. Use
              apenas logomarcas institucionais autorizadas.
            </p>
            {source && (
              <div className="actions-row">
                <Image
                  unoptimized
                  src={source}
                  width={120}
                  height={80}
                  style={{ objectFit: "contain" }}
                  alt={`Prévia da marca: ${brand.nome}`}
                />
                <Button
                  onClick={() =>
                    changeBrand(slot, { logo_id: null, conteudo_base64: null })
                  }
                >
                  Remover logo de {label.toLowerCase()}
                </Button>
              </div>
            )}
            <FormControlLabel
              control={
                <Checkbox
                  checked={brand.divulgacao_autorizada}
                  disabled={!brand.nome || !brand.uso_autorizado}
                  onChange={(_, checked) =>
                    changeBrand(slot, { divulgacao_autorizada: checked })
                  }
                />
              }
              label={`Divulgação pública de ${label.toLowerCase()} autorizada`}
            />
          </fieldset>
        );
      })}
      {failure && <Alert severity="error">{failure}</Alert>}
      <p className="muted">
        As autorizações de divulgação ficam registradas para revisão. A
        publicação de novos metadados depende da homologação do fluxo
        institucional.
      </p>
    </fieldset>
  );
}
