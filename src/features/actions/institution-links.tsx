"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  TextField,
} from "@mui/material";
import { api, errorMessage } from "@/lib/api";
import {
  emptyLink,
  institutionTypes,
  type InstitutionLink,
} from "./institutional";

type Suggestion = {
  id: string;
  nome: string;
  tipo: InstitutionLink["tipo"];
  logo_id: string | null;
  origem: string;
  correspondencia: string;
};

function InstitutionRow({
  value,
  index,
  supporter,
  onChange,
  onRemove,
  removable,
}: {
  value: InstitutionLink;
  index: number;
  supporter: boolean;
  onChange: (value: InstitutionLink) => void;
  onRemove: () => void;
  removable: boolean;
}) {
  const title = `${supporter ? "Apoiador" : "Contratante"} ${index + 1}`;
  const [term, setTerm] = useState("");
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [failure, setFailure] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setTerm(value.nome.trim()), 350);
    return () => clearTimeout(timer);
  }, [value.nome]);
  const matches = useQuery({
    queryKey: ["instituicoes", term],
    enabled: term.length >= 2 && !value.instituicao_id,
    queryFn: async ({ signal }) =>
      (
        await api.get<{ items: Suggestion[] }>("/instituicoes", {
          signal,
          params: { busca: term },
        })
      ).data,
    staleTime: 30_000,
  });
  function change(patch: Partial<InstitutionLink>) {
    onChange({ ...value, ...patch });
  }
  async function upload(file?: File) {
    setFailure("");
    if (!file) return;
    if (
      file.size > 262144 ||
      !["image/png", "image/jpeg"].includes(file.type)
    ) {
      setFailure(
        "Use PNG/JPEG estático, 64 a 2048 pixels por lado, até 256 KiB.",
      );
      return;
    }
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      change({
        logo_id: null,
        conteudo_base64: btoa(
          Array.from(bytes, (byte) => String.fromCharCode(byte)).join(""),
        ),
      });
    } catch {
      setFailure("Não foi possível abrir a imagem.");
    }
  }
  const source = value.conteudo_base64
    ? `data:image/png;base64,${value.conteudo_base64}`
    : value.logo_id && value.instituicao_id
      ? `/api/backend/instituicoes/${value.instituicao_id}/marcas/${value.logo_id}`
      : null;
  return (
    <fieldset className="institutional-fields">
      <legend>{title}</legend>
      <TextField
        label={`Instituição ${title.toLowerCase()}`}
        required
        value={value.nome}
        onChange={(event) => {
          setSuggestion(null);
          change({
            nome: event.target.value,
            instituicao_id: null,
            logo_id: null,
            conteudo_base64: null,
          });
        }}
        slotProps={{ htmlInput: { maxLength: 160, minLength: 2 } }}
      />
      <TextField
        select
        required
        label={`Tipo da instituição ${title.toLowerCase()}`}
        value={value.tipo}
        onChange={(event) => {
          setSuggestion(null);
          change({
            tipo: event.target.value as InstitutionLink["tipo"],
            instituicao_id: null,
            logo_id: null,
            conteudo_base64: null,
          });
        }}
      >
        {Object.entries(institutionTypes).map(([key, label]) => (
          <MenuItem key={key} value={key}>
            {label}
          </MenuItem>
        ))}
      </TextField>
      {!value.instituicao_id && term.length >= 2 && (
        <div aria-live="polite">
          {matches.isFetching ? (
            <p>Buscando instituições…</p>
          ) : matches.isError ? (
            <Alert severity="warning">
              {errorMessage(matches.error)} O cadastro manual continua
              disponível.
            </Alert>
          ) : matches.data?.items.length ? (
            matches.data.items.map((item) => (
              <div key={item.id} className="panel">
                <p>
                  <strong>{item.nome}</strong> · {institutionTypes[item.tipo]} ·{" "}
                  {item.correspondencia === "EXATA"
                    ? "Correspondência exata"
                    : "Correspondência aproximada"}
                </p>
                <p className="muted">
                  Origem: base interna.{" "}
                  {item.logo_id
                    ? "Imagem enviada anteriormente; confira a identidade e a autorização de uso."
                    : "Sem logo cadastrada."}
                </p>
                {item.logo_id && (
                  <Image
                    unoptimized
                    src={`/api/backend/instituicoes/${item.id}/marcas/${item.logo_id}`}
                    width={100}
                    height={70}
                    style={{ objectFit: "contain" }}
                    alt={`Sugestão de logo de ${item.nome}`}
                  />
                )}
                <Button
                  onClick={() => {
                    setSuggestion(item);
                    change({
                      nome: item.nome,
                      tipo: item.tipo,
                      instituicao_id: item.id,
                      logo_id: null,
                      conteudo_base64: null,
                    });
                  }}
                >
                  Selecionar instituição {item.nome}
                </Button>
              </div>
            ))
          ) : (
            <p className="muted">
              Nenhuma correspondência. Continue com a instituição informada e
              envie uma logo, se desejar.
            </p>
          )}
        </div>
      )}
      {supporter && (
        <TextField
          select
          required
          label={`Modalidade de apoio ${index + 1}`}
          value={value.modalidade || ""}
          onChange={(event) =>
            change({ modalidade: event.target.value as "TOTAL" | "PARCIAL" })
          }
        >
          <MenuItem value="">Selecione</MenuItem>
          <MenuItem value="TOTAL">Total</MenuItem>
          <MenuItem value="PARCIAL">Parcial</MenuItem>
        </TextField>
      )}
      <FormControlLabel
        control={
          <Checkbox
            checked={value.uso_autorizado}
            onChange={(_, checked) =>
              change(
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
        label={`Uso da marca de ${title.toLowerCase()} autorizado`}
      />
      {suggestion?.logo_id && (
        <Button
          disabled={!value.uso_autorizado}
          onClick={() =>
            change({ logo_id: suggestion.logo_id, conteudo_base64: null })
          }
        >
          Usar logo sugerida de {suggestion.nome}
        </Button>
      )}
      <label className="logo-upload">
        Enviar outra logo de {title.toLowerCase()}
        <input
          type="file"
          accept="image/png,image/jpeg"
          disabled={!value.nome.trim() || !value.uso_autorizado}
          onChange={(event) => {
            void upload(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </label>
      <p className="muted">
        PNG/JPEG estático, 64 a 2048 pixels por lado, até 256 KiB. O formulário
        completo admite até 1 MiB por gravação.
      </p>
      {source && (
        <div className="actions-row">
          <Image
            unoptimized
            src={source}
            width={120}
            height={80}
            style={{ objectFit: "contain" }}
            alt={`Prévia da marca: ${value.nome}`}
          />
          <Button
            onClick={() => change({ logo_id: null, conteudo_base64: null })}
          >
            Remover logo de {title.toLowerCase()}
          </Button>
        </div>
      )}
      <FormControlLabel
        control={
          <Checkbox
            checked={value.divulgacao_autorizada}
            disabled={!value.uso_autorizado || !value.nome.trim()}
            onChange={(_, checked) =>
              change({ divulgacao_autorizada: checked })
            }
          />
        }
        label={`Divulgação pública de ${title.toLowerCase()} autorizada`}
      />
      {failure && <Alert severity="error">{failure}</Alert>}
      <Button disabled={!removable} onClick={onRemove}>
        Remover {title.toLowerCase()}
      </Button>
    </fieldset>
  );
}

export function InstitutionLinks({
  value,
  onChange,
  supporter = false,
}: {
  value: InstitutionLink[];
  onChange: (value: InstitutionLink[]) => void;
  supporter?: boolean;
}) {
  // Chaves locais preservam upload/busca de cada bloco durante remoções.
  const [keys, setKeys] = useState(() => value.map(() => crypto.randomUUID()));
  return (
    <fieldset className="institutional-fields">
      <legend>{supporter ? "Apoiadores" : "Contratantes"}</legend>
      {value.map((link, index) => (
        <InstitutionRow
          key={keys[index] || index}
          value={link}
          index={index}
          supporter={supporter}
          removable={value.length > 1}
          onChange={(next) =>
            onChange(value.map((old, i) => (i === index ? next : old)))
          }
          onRemove={() => {
            setKeys(keys.filter((_, i) => i !== index));
            onChange(value.filter((_, i) => i !== index));
          }}
        />
      ))}
      <Button
        onClick={() => {
          setKeys([...keys, crypto.randomUUID()]);
          onChange([...value, emptyLink()]);
        }}
        disabled={value.length >= 100}
      >
        Adicionar {supporter ? "apoiador" : "contratante"}
      </Button>
      {!value.length && (
        <Alert severity="warning">
          Cadastre ao menos um {supporter ? "apoiador" : "contratante"}. O
          legado foi preservado para revisão.
        </Alert>
      )}
    </fieldset>
  );
}
