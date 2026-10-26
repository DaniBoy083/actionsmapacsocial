"use client";
import { useRef, useState, useSyncExternalStore } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  FormControlLabel,
  LinearProgress,
  MenuItem,
  Step,
  StepLabel,
  Stepper,
  TextField,
} from "@mui/material";
import { FiFileText, FiRotateCw, FiUpload } from "react-icons/fi";
import { api, errorMessage, type Action, type Municipality } from "@/lib/api";
import { useSession } from "@/components/session-context";
import { ActionDialog } from "@/features/actions/action-dialog";
import { RecordFields, type RecordRow } from "@/features/imports/record-fields";

type Preview = {
  id: string;
  formato: "pdf" | "csv" | "json";
  paginas: number;
  registros: RecordRow[];
  possiveis_duplicidades: number[];
  producao: boolean;
  expira_em: string;
};
type Report = { incluidos: number; existentes: number; pendentes: number };
const MAX_FILE = 8 * 1024 * 1024;
const subscribeHydration = () => () => {};
const readyInBrowser = () => true;
const notReadyOnServer = () => false;

export function ImportWizard() {
  const hydrated = useSyncExternalStore(
    subscribeHydration,
    readyInBrowser,
    notReadyOnServer,
  );
  const session = useSession();
  const queries = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [rows, setRows] = useState<RecordRow[]>([]);
  const [step, setStep] = useState(0);
  const [page, setPage] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [destination, setDestination] = useState("");
  const [actionSearch, setActionSearch] = useState("");
  const [creatingAction, setCreatingAction] = useState(false);
  const [productionApproved, setProductionApproved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [failure, setFailure] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [imageReady, setImageReady] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const headers = { "X-CSRF-Token": session.csrf_token };
  const actions = useQuery({
    queryKey: ["acoes", "import-destinations", actionSearch],
    queryFn: async () =>
      (
        await api.get<{ items: Action[]; total: number }>("/acoes", {
          params: { tamanho: 100, busca: actionSearch || undefined },
        })
      ).data,
  });
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  const current = rows[page - 1];
  const selected = rows.filter(
    (row) => row.revisado && row.nome.trim().length >= 2,
  );
  const destinationAction = actions.data?.items.find(
    (item) => item.id === destination,
  );

  function updateCurrent(values: Partial<RecordRow>) {
    setRows((previous) =>
      previous.map((row) =>
        row.pagina === page ? { ...row, revisado: false, ...values } : row,
      ),
    );
    setProductionApproved(false);
  }
  function changePage(value: number) {
    setPage(value);
    setRotation(0);
    setImageReady(false);
    setImageFailed(false);
  }
  function template() {
    const url = URL.createObjectURL(
      new Blob(
        ["\uFEFFnome;municipio_residencia_ibge\nPessoa de exemplo;2508901\n"],
        { type: "text/csv;charset=utf-8" },
      ),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "modelo-beneficiarios.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  async function prepare() {
    if (!file) return;
    const kind = file.name.split(".").pop()?.toLowerCase();
    if (
      !["pdf", "csv", "json"].includes(kind || "") ||
      !file.size ||
      file.size > MAX_FILE
    ) {
      setFailure("Selecione um PDF, CSV ou JSON de até 8 MiB.");
      return;
    }
    setBusy(true);
    setFailure("");
    setProgress(0);
    let identifier: string | null = null;
    try {
      const content = await file.arrayBuffer();
      const digest = await crypto.subtle.digest("SHA-256", content);
      const hash = Array.from(new Uint8Array(digest))
        .map((v) => v.toString(16).padStart(2, "0"))
        .join("");
      const { data: upload } = await api.post<{
        id: string;
        tamanho_parte: number;
        partes: number;
      }>(
        "/importacoes/arquivos",
        { formato: kind, tamanho: file.size, hash_arquivo: hash },
        { headers },
      );
      identifier = upload.id;
      for (let index = 0; index < upload.partes; index++) {
        const start = index * upload.tamanho_parte;
        await api.put(
          `/importacoes/${upload.id}/partes/${index}`,
          content.slice(start, start + upload.tamanho_parte),
          {
            headers: { ...headers, "Content-Type": "application/octet-stream" },
          },
        );
        setProgress(Math.round(((index + 1) / upload.partes) * 100));
      }
      const { data } = await api.post<Preview>(
        `/importacoes/${upload.id}/preparar`,
        {},
        { headers },
      );
      setPreview(data);
      setRows(
        data.formato === "pdf"
          ? Array.from({ length: data.paginas }, (_, index) => ({
              pagina: index + 1,
              nome: "",
              municipio_residencia_ibge: null,
              local_indice: null,
              revisado: false,
            }))
          : data.registros,
      );
      changePage(1);
      setStep(1);
    } catch (error) {
      setFailure(errorMessage(error));
      if (identifier) {
        try {
          await api.delete(`/importacoes/${identifier}`, { headers });
        } catch {
          /* Expira automaticamente. */
        }
      }
    } finally {
      setBusy(false);
    }
  }
  async function discard() {
    if (
      !preview ||
      !window.confirm(
        "Remover o arquivo temporário e descartar esta revisão? Os registros já importados serão preservados.",
      )
    )
      return;
    setBusy(true);
    try {
      await api.delete(`/importacoes/${preview.id}`, { headers });
      setPreview(null);
      setRows([]);
      setFile(null);
      setStep(0);
      setFailure("");
      setReport(null);
      setProductionApproved(false);
      if (input.current) input.current.value = "";
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (
      !preview ||
      !selected.length ||
      !destinationAction ||
      (preview.producao && !productionApproved)
    )
      return;
    setBusy(true);
    setFailure("");
    try {
      const { data } = await api.post<Report>(
        "/importacoes/confirmar",
        {
          importacao_id: preview.id,
          acao_id: destination,
          registros: selected,
          confirmacao_producao: productionApproved,
        },
        { headers },
      );
      setReport(data);
      setStep(3);
      setRows((previous) =>
        previous.map((row) => ({ ...row, revisado: false })),
      );
      setProductionApproved(false);
      await Promise.all(
        ["acoes", "beneficiarios", "indicadores"].map((key) =>
          queries.invalidateQueries({ queryKey: [key] }),
        ),
      );
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Importar dados</h1>
          <p>
            Envie um arquivo, confira os dados e associe os beneficiários a uma
            ação.
          </p>
        </div>
      </div>
      <section className="panel">
        <Stepper className="import-steps" activeStep={step} alternativeLabel>
          {["Arquivo", "Conferir", "Revisar", "Resultado"].map((label) => (
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
      {actions.isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMessage(actions.error)}{" "}
          <Button onClick={() => actions.refetch()}>Recarregar ações</Button>
        </Alert>
      )}
      {!preview ? (
        <section className="panel upload-panel">
          <FiUpload className="upload-icon" aria-hidden="true" />
          <h2>Inserir dados por arquivo</h2>
          <p className="muted">
            PDF digitalizado para transcrição conferida, ou CSV/JSON com nomes e
            municípios. Até 8 MiB e 200 páginas ou registros por arquivo.
          </p>
          <div className="form-grid">
            <label htmlFor="import-file">
              Selecionar arquivo PDF, CSV ou JSON
            </label>
            <input
              ref={input}
              id="import-file"
              type="file"
              accept=".pdf,.csv,.json"
              disabled={busy || !hydrated}
              onChange={(event) => {
                setFile(event.target.files?.[0] || null);
                setFailure("");
              }}
            />
            <Alert severity="info">
              Use somente nome e município de residência opcional. Não inclua
              CPF, telefone, receitas ou outros campos clínicos em CSV/JSON.
              Nomes do PDF são conferidos manualmente.
            </Alert>
            <div className="actions-row">
              <Button
                variant="contained"
                startIcon={<FiFileText />}
                disabled={busy || !file}
                onClick={prepare}
              >
                {busy ? "Enviando e analisando…" : "Analisar arquivo"}
              </Button>
              <Button disabled={busy} onClick={template}>
                Baixar modelo CSV
              </Button>
            </div>
            {busy && (
              <div role="status" aria-live="polite">
                <p>
                  Envio: {progress}%
                  {progress === 100 ? " · Analisando arquivo…" : ""}
                </p>
                <LinearProgress
                  aria-label="Progresso do envio"
                  variant="determinate"
                  value={progress}
                />
              </div>
            )}
            <p className="muted">
              O envio prepara uma prévia. Nenhum beneficiário é cadastrado até
              sua confirmação. O arquivo temporário fica privado e expira em 24
              horas.
            </p>
          </div>
        </section>
      ) : (
        <>
          <section className="panel">
            <h2>
              {preview.formato.toUpperCase()} · {preview.paginas}{" "}
              {preview.formato === "pdf" ? "páginas" : "registros"}
            </h2>
            <p className="muted">
              {selected.length} selecionados neste lote. Campos não conferidos
              ficam pendentes. Expiração:{" "}
              {new Date(preview.expira_em).toLocaleString("pt-BR")}.
            </p>
            {preview.possiveis_duplicidades.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Nomes repetidos nos registros{" "}
                {preview.possiveis_duplicidades.join(", ")}. Confira se são
                pessoas distintas. O sistema não une pessoas pelo nome.
              </Alert>
            )}
            <div className="actions-row">
              <Button disabled={busy} onClick={discard}>
                Remover arquivo temporário
              </Button>
            </div>
          </section>
          {step === 3 && report ? (
            <section className="panel" aria-live="polite">
              <h2>Resultado da importação</h2>
              <Alert severity="success">
                {report.incluidos} registro(s) incluído(s). {report.existentes}{" "}
                já associado(s). {report.pendentes} pendente(s) neste arquivo
                para esta ação.
              </Alert>
              <Button sx={{ mt: 2 }} onClick={() => setStep(1)}>
                Revisar outros registros
              </Button>
            </section>
          ) : (
            <>
              <section className="panel">
                <TextField
                  label="Buscar ação de destino"
                  value={actionSearch}
                  disabled={busy || step === 2}
                  fullWidth
                  sx={{ mb: 2 }}
                  onChange={(event) => {
                    setActionSearch(event.target.value);
                    setDestination("");
                  }}
                  helperText="Digite parte do nome para localizar a ação."
                />
                {(actions.data?.total || 0) > 100 && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Mostrando até 100 ações. Refine a busca para localizar o
                    destino.
                  </Alert>
                )}
                <div className="actions-row">
                  <TextField
                    select
                    label="Ação de destino"
                    value={destination}
                    disabled={busy || step === 2}
                    sx={{ minWidth: 240, flex: 1 }}
                    onChange={(event) => {
                      setDestination(event.target.value);
                      setProductionApproved(false);
                    }}
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
                  <Button
                    disabled={busy || step === 2}
                    onClick={() => setCreatingAction(true)}
                  >
                    Cadastrar nova ação
                  </Button>
                </div>
              </section>
              {step === 1 && current ? (
                <>
                  <section className="panel">
                    <div className="actions-row">
                      <Button
                        disabled={page === 1}
                        onClick={() => changePage(page - 1)}
                      >
                        Anterior
                      </Button>
                      <strong aria-live="polite">
                        {preview.formato === "pdf" ? "Página" : "Registro"}{" "}
                        {page} de {preview.paginas}
                      </strong>
                      <Button
                        disabled={page === preview.paginas}
                        onClick={() => changePage(page + 1)}
                      >
                        Próximo
                      </Button>
                    </div>
                  </section>
                  <div
                    className={preview.formato === "pdf" ? "import-grid" : ""}
                  >
                    {preview.formato === "pdf" && (
                      <section className="panel">
                        <div className="actions-row">
                          <h2>Conferir página</h2>
                          <Button
                            startIcon={<FiRotateCw />}
                            onClick={() => {
                              setRotation((rotation + 90) % 360);
                              setImageReady(false);
                              setImageFailed(false);
                            }}
                          >
                            Girar página
                          </Button>
                        </div>
                        {imageFailed && (
                          <Alert severity="error">
                            Não foi possível abrir a página. Tente girar a
                            página ou reenvie o arquivo.
                          </Alert>
                        )}
                        {/* Imagem privada autenticada, sem otimização/cache compartilhado. */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          className="import-image"
                          key={`${page}:${rotation}`}
                          src={`/api/backend/importacoes/${preview.id}/paginas/${page}?rotacao=${rotation}`}
                          alt={`Documento enviado, página ${page}`}
                          onLoad={() => setImageReady(true)}
                          onError={() => {
                            setImageFailed(true);
                            setImageReady(false);
                            updateCurrent({ revisado: false });
                          }}
                        />
                      </section>
                    )}
                    <section className="panel">
                      <h2>Conferir campos gerais</h2>
                      <RecordFields
                        key={page}
                        row={current}
                        municipalities={municipalities.data || []}
                        canReview={
                          preview.formato !== "pdf" ||
                          (imageReady && !imageFailed)
                        }
                        onChange={updateCurrent}
                      />
                      {municipalities.isError && (
                        <Alert severity="error">
                          {errorMessage(municipalities.error)}{" "}
                          <Button onClick={() => municipalities.refetch()}>
                            Tentar novamente
                          </Button>
                        </Alert>
                      )}
                    </section>
                  </div>
                  <section className="panel">
                    <Button
                      variant="contained"
                      disabled={!selected.length || !destinationAction}
                      onClick={() => {
                        setStep(2);
                        setProductionApproved(false);
                      }}
                    >
                      Revisar lote ({selected.length})
                    </Button>
                  </section>
                </>
              ) : (
                step === 2 && (
                  <section className="panel">
                    <h2>Revisar e confirmar</h2>
                    <p>
                      Ação: <strong>{destinationAction?.nome}</strong>. Confira
                      a correspondência e possíveis duplicidades.
                    </p>
                    <div className="table-scroll">
                      <table className="data-table">
                        <caption className="sr-only">
                          Registros selecionados para importação
                        </caption>
                        <thead>
                          <tr>
                            <th scope="col">Origem</th>
                            <th scope="col">Nome</th>
                            <th scope="col">Município de residência</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selected.map((row) => (
                            <tr key={row.pagina}>
                              <td>{row.pagina}</td>
                              <td>{row.nome}</td>
                              <td>
                                {municipalities.data?.find(
                                  (m) =>
                                    m.codigo === row.municipio_residencia_ibge,
                                )?.nome || "Não identificado"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {preview.producao && (
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={productionApproved}
                            onChange={(event) =>
                              setProductionApproved(event.target.checked)
                            }
                            disabled={busy}
                          />
                        }
                        label="Conferi os registros e autorizo expressamente sua gravação no banco de produção."
                      />
                    )}
                    <div className="actions-row" style={{ marginTop: 20 }}>
                      <Button disabled={busy} onClick={() => setStep(1)}>
                        Corrigir revisão
                      </Button>
                      <Button
                        variant="contained"
                        disabled={
                          busy || (preview.producao && !productionApproved)
                        }
                        onClick={confirm}
                      >
                        {busy ? "Importando…" : "Confirmar importação"}
                      </Button>
                    </div>
                  </section>
                )
              )}
            </>
          )}
        </>
      )}
      {creatingAction && (
        <ActionDialog onClose={() => setCreatingAction(false)} />
      )}
    </>
  );
}
