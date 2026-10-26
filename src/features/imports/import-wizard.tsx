"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Step,
  StepLabel,
  Stepper,
  TextField,
} from "@mui/material";
import { api, errorMessage, type Action, type Municipality } from "@/lib/api";
import { useSession } from "@/components/session-context";

type Preview = {
  id: string;
  paginas: number;
  documento: string;
  avisos: string[];
};
type Report = { incluidos: number; existentes: number; pendentes: number };
export function ImportWizard() {
  const session = useSession();
  const client = useQueryClient();
  const [preview, setPreview] = useState<Preview | null>(null);
  const [step, setStep] = useState(0);
  const [page, setPage] = useState(1);
  const [destination, setDestination] = useState("");
  const [name, setName] = useState("");
  const [municipality, setMunicipality] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [imageFailed, setImageFailed] = useState(false);
  const actions = useQuery({
    queryKey: ["acoes", "import-destinations"],
    queryFn: async () =>
      (
        await api.get<{ items: Action[] }>("/acoes", {
          params: { tamanho: 100 },
        })
      ).data,
  });
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  async function prepare() {
    setBusy(true);
    setFailure("");
    try {
      const { data } = await api.post<Preview>(
        "/importacoes/preview",
        {},
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      setPreview(data);
      setStep(1);
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!preview || !reviewed || !destination || name.trim().length < 2) return;
    setBusy(true);
    setFailure("");
    try {
      const { data } = await api.post<Report>(
        "/importacoes/confirmar",
        {
          importacao_id: preview.id,
          acao_id: destination,
          registros: [
            {
              pagina: page,
              nome: name.trim(),
              municipio_residencia_ibge: municipality || null,
              local_indice: null,
              revisado: true,
            },
          ],
        },
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      setReport(data);
      setStep(3);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["acoes"] }),
        client.invalidateQueries({ queryKey: ["beneficiarios"] }),
        client.invalidateQueries({ queryKey: ["indicadores"] }),
      ]);
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  function changePage(value: number) {
    if (
      name &&
      !window.confirm(
        "Descartar a transcrição ainda não importada desta página?",
      )
    )
      return;
    setPage(value);
    setName("");
    setMunicipality("");
    setReviewed(false);
    setImageFailed(false);
    setReport(null);
    setStep(1);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Cadastrar dados iniciais</h1>
          <p>
            Revise as fichas históricas antes de registrar beneficiários nas
            ações.
          </p>
        </div>
      </div>
      <section className="panel">
        <Stepper activeStep={step} alternativeLabel>
          {["Documento", "Conferência", "Revisão", "Resultado"].map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </section>
      {failure && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {failure}
        </Alert>
      )}
      {!preview ? (
        <section className="panel">
          <h2>Documento histórico autorizado</h2>
          <p className="muted">
            Programa Melhor VISÃO. O documento é aberto em ambiente restrito,
            página a página. A transcrição dos campos gerais é manual e deve
            preservar as dúvidas de leitura.
          </p>
          <Alert severity="warning" sx={{ mb: 3 }}>
            Esta etapa registra dados somente no armazenamento local de
            desenvolvimento. A importação institucional exige homologação,
            backup e autorização específica.
          </Alert>
          <Button variant="contained" onClick={prepare} disabled={busy}>
            {busy ? "Preparando documento…" : "Preparar documento histórico"}
          </Button>
        </section>
      ) : (
        <>
          <section className="panel">
            <h2>
              {preview.documento} · {preview.paginas} páginas
            </h2>
            <p className="muted">
              Origem: documento histórico / página {page}. Campos ilegíveis
              devem aguardar revisão. Não transcreva receitas, CPF, contatos ou
              informações clínicas.
            </p>
            <div className="actions-row">
              <Button
                disabled={busy || page === 1}
                onClick={() => changePage(page - 1)}
              >
                Página anterior
              </Button>
              <Button
                disabled={busy || page === preview.paginas}
                onClick={() => changePage(page + 1)}
              >
                Próxima página
              </Button>
            </div>
          </section>
          {step === 3 && report ? (
            <section className="panel">
              <h2>Resultado do lote</h2>
              <Alert severity="success">
                {report.incluidos} registro incluído. {report.existentes}{" "}
                registro já associado a esta ação.
              </Alert>
              <p className="muted">
                As demais páginas não foram processadas neste lote. A mesma
                página na mesma ação não é importada novamente.
              </p>
              <Button
                variant="contained"
                disabled={page === preview.paginas}
                onClick={() => changePage(page + 1)}
              >
                Conferir próxima página
              </Button>
              <Button onClick={() => setStep(1)}>Voltar à página atual</Button>
            </section>
          ) : (
            <div className="import-grid">
              <section className="panel">
                <h2>Conferir documento</h2>
                {imageFailed ? (
                  <Alert severity="error">
                    Não foi possível abrir a página. Recarregue o documento
                    antes de importar.
                  </Alert>
                ) : (
                  <>
                    {/* Imagem privada autenticada; sem otimizador/cache compartilhado. */}
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      className="import-image"
                      key={page}
                      src={`/api/backend/importacoes/${preview.id}/paginas/${page}`}
                      alt={`Ficha histórica, página ${page}. Consulte e transcreva somente campos gerais legíveis.`}
                      onError={() => setImageFailed(true)}
                    />
                  </>
                )}
              </section>
              <section className="panel">
                <h2>{step === 2 ? "Revisar e confirmar" : "Campos gerais"}</h2>
                <div className="form-grid">
                  <TextField
                    select
                    label="Ação de destino"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    disabled={busy || step === 2}
                  >
                    <MenuItem value="">Selecione uma ação</MenuItem>
                    {actions.data?.items
                      .filter((row) => row.status !== "arquivada")
                      .map((row) => (
                        <MenuItem key={row.id} value={row.id}>
                          {row.nome}
                        </MenuItem>
                      ))}
                  </TextField>
                  <TextField
                    label="Nome conferido no documento"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={busy || step === 2}
                    helperText="Se estiver ilegível, deixe esta página para revisão."
                  />
                  <TextField
                    select
                    label="Município de residência informado"
                    value={municipality}
                    onChange={(e) => setMunicipality(e.target.value)}
                    disabled={busy || step === 2}
                  >
                    <MenuItem value="">Não identificado / revisar</MenuItem>
                    {municipalities.data?.map((p) => (
                      <MenuItem key={p.codigo} value={p.codigo}>
                        {p.nome}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Alert severity="info">
                    A localização do beneficiário não será atribuída
                    automaticamente ao local da ação. Reimportações são
                    verificadas por documento, página e ação; nomes iguais
                    exigem conferência humana.
                  </Alert>
                  {step === 1 ? (
                    <Button
                      variant="contained"
                      disabled={
                        !destination || name.trim().length < 2 || imageFailed
                      }
                      onClick={() => setStep(2)}
                    >
                      Revisar correspondência
                    </Button>
                  ) : (
                    <>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={reviewed}
                            onChange={(e) => setReviewed(e.target.checked)}
                          />
                        }
                        label="Conferi a página, o nome, a ação de destino e possíveis duplicidades."
                      />
                      <Button disabled={busy} onClick={() => setStep(1)}>
                        Corrigir dados
                      </Button>
                      <Button
                        variant="contained"
                        disabled={busy || !reviewed || imageFailed}
                        onClick={confirm}
                      >
                        {busy ? "Importando…" : "Confirmar importação local"}
                      </Button>
                    </>
                  )}
                </div>
              </section>
            </div>
          )}
        </>
      )}
    </>
  );
}
