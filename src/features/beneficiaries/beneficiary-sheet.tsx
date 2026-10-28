"use client";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { api, dateLabel, errorMessage } from "@/lib/api";
import type { BeneficiarySheet as Sheet } from "./registration";
import "./beneficiary-sheet.css";

const shown = (value: string | null) => value || "Não informado";
function receipt(value: boolean | null) {
  return value === true
    ? "Confirmado no cadastro"
    : value === false
      ? "Não confirmado"
      : "Não informado";
}
export function BeneficiarySheet({
  actionId,
  personId,
  secondCopy,
  onClose,
}: {
  actionId: string;
  personId: string;
  secondCopy: boolean;
  onClose: () => void;
}) {
  const query = useQuery({
    queryKey: ["beneficiary-sheet", actionId, personId, secondCopy],
    gcTime: 0,
    staleTime: 0,
    retry: false,
    queryFn: async ({ signal }) =>
      (
        await api.get<Sheet>(
          `/acoes/${actionId}/beneficiarios/${personId}${secondCopy ? "/segunda-via" : ""}`,
          { signal },
        )
      ).data,
  });
  const data = query.data;
  const title = secondCopy
    ? "Segunda via da ficha de cadastro"
    : "Ficha de cadastro do beneficiário";
  return (
    <Dialog
      open
      onClose={onClose}
      fullWidth
      maxWidth="md"
      aria-labelledby="beneficiary-sheet-title"
    >
      <DialogTitle id="beneficiary-sheet-title" data-print-controls>
        {title}
      </DialogTitle>
      <DialogContent
        tabIndex={0}
        role="region"
        aria-label="Conteúdo da ficha de cadastro"
      >
        {query.isPending ? (
          <p role="status">Carregando ficha…</p>
        ) : query.isError ? (
          <Alert severity="error">{errorMessage(query.error)}</Alert>
        ) : (
          data && (
            <article className="beneficiary-sheet" data-beneficiary-print>
              <header>
                <strong>AC SOCIAL · AC ACTIONS MAP</strong>
                <h1>{title}</h1>
                <p>
                  Programa / ação: <strong>{data.acao.nome}</strong>
                </p>
              </header>
              <dl className="beneficiary-sheet-fields">
                {[
                  ["Nome", data.nome],
                  [
                    "CPF",
                    data.cpf
                      ? data.cpf.replace(
                          /(\d{3})(\d{3})(\d{3})(\d{2})/,
                          "$1.$2.$3-$4",
                        )
                      : null,
                  ],
                  [
                    "CPF do documento (pendente de conferência)",
                    data.cpf_documento,
                  ],
                  ["Telefone", data.telefone],
                  [
                    "Data de nascimento",
                    data.data_nascimento
                      ? dateLabel(data.data_nascimento)
                      : null,
                  ],
                  [
                    "Data da ficha",
                    data.data_ficha ? dateLabel(data.data_ficha) : null,
                  ],
                  ["Município indicado na ficha", data.municipio_ficha_nome],
                  ["Município de residência", data.municipio_residencia_nome],
                  ["Responsável indicado na ficha", data.responsavel],
                  [
                    "Declaração de recebimento",
                    receipt(data.recebimento_confirmado),
                  ],
                  ["Observações gerais", data.observacoes],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{shown(value)}</dd>
                  </div>
                ))}
              </dl>
              {secondCopy && (
                <section className="beneficiary-receipt">
                  <h2>Declaração de recebimento</h2>
                  <p>
                    Declaro ter recebido os benefícios da ação institucional
                    acima identificada.
                  </p>
                  <p>
                    Local e data:
                    ____________________________________________________
                  </p>
                  <p className="beneficiary-signature">
                    Assinatura do beneficiário ou responsável nesta via
                  </p>
                  <p className="beneficiary-sheet-note">
                    Espaço para nova assinatura. Esta emissão não reproduz a
                    assinatura original nem altera a confirmação de recebimento
                    no cadastro.
                  </p>
                </section>
              )}
              <footer>
                <p>
                  Dados atuais do cadastro · revisão {data.versao}. Campos
                  ausentes permanecem como não informados.
                </p>
                {data.emitido_em && (
                  <p>
                    Emitida em{" "}
                    {new Intl.DateTimeFormat("pt-BR", {
                      dateStyle: "short",
                      timeStyle: "short",
                      timeZone: "America/Sao_Paulo",
                    }).format(new Date(data.emitido_em))}{" "}
                    (Brasília).
                  </p>
                )}
                <p>
                  Documento de uso restrito. Guarde a via impressa sob os
                  cuidados da instituição.
                </p>
              </footer>
            </article>
          )
        )}
      </DialogContent>
      <DialogActions data-print-controls sx={{ p: 3 }}>
        <Button onClick={onClose}>Fechar</Button>
        {secondCopy && (
          <Button
            variant="contained"
            disabled={!data || query.isFetching || query.isError}
            onClick={() => window.print()}
          >
            Imprimir segunda via
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
