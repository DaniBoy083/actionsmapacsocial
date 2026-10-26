"use client";

import { useEffect, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import toast from "react-hot-toast";
import { api, dateLabel, errorMessage } from "@/lib/api";

type Credential = {
  id: string;
  nome: string;
  token_mascarado: string;
  escopo: string;
  criado_em: string;
  expira_em: string | null;
  ultimo_uso_em: string | null;
  chamadas: number;
  status: "ativa" | "expirada" | "revogada";
};
type Operation = {
  type: "criar" | "rotacionar" | "revogar";
  credential?: Credential;
};
type Issued = { credencial: Credential; token: string };
const credentialSchema = z.object({
  nome: z
    .string()
    .trim()
    .min(3, "Informe um nome com pelo menos três caracteres.")
    .max(80),
  validade_dias: z.number().int().min(1).max(365).nullable(),
  password: z.string().min(1, "Confirme sua senha institucional.").max(1024),
});
type CredentialForm = z.infer<typeof credentialSchema>;

function expirationLabel(value: string | null) {
  return value === null ? "Nunca expira" : dateLabel(value);
}

function curl(endpoint: string, token = "<TOKEN_DA_AGENDA>") {
  // URLs vêm da origem de configuração; a lista não aceita entrada livre do usuário.
  return `curl.exe --fail-with-body --request GET '${endpoint.replaceAll("'", "%27")}' --header 'Accept: application/json' --header 'Authorization: Bearer ${token}'`;
}

export async function copyIntegrationText(value: string) {
  try {
    await navigator.clipboard.writeText(value);
    toast.success("Copiado para a área de transferência.");
  } catch {
    toast.error(
      "Não foi possível copiar. Selecione o texto do campo e copie manualmente.",
    );
  }
}

export function IntegrationResources({
  endpoints,
}: {
  endpoints: { saude: string; resumos: string };
}) {
  return (
    <section className="panel">
      <h2>Endpoints para a Agenda consultar o Map</h2>
      <p className="muted">
        Use um token de leitura criado abaixo no servidor da Agenda. Os comandos
        usam um marcador para você substituir pelo token salvo.
      </p>
      {(
        [
          ["Saúde da integração", endpoints.saude],
          ["Resumos de ações", endpoints.resumos],
        ] as const
      ).map(([label, endpoint]) => (
        <div className="integration-resource" key={endpoint}>
          <h3>{label}</h3>
          <TextField
            label={`Endpoint — ${label}`}
            value={endpoint}
            fullWidth
            slotProps={{ input: { readOnly: true } }}
            onFocus={(event) => event.target.select()}
          />
          <Stack
            direction="row"
            useFlexGap
            sx={{ my: 1, flexWrap: "wrap", gap: 1 }}
          >
            <Button
              variant="outlined"
              onClick={() => copyIntegrationText(endpoint)}
            >
              Copiar endpoint — {label}
            </Button>
            <Button onClick={() => copyIntegrationText(curl(endpoint))}>
              Copiar cURL — {label}
            </Button>
          </Stack>
          <TextField
            label={`cURL — ${label}`}
            value={curl(endpoint)}
            helperText="Comando para PowerShell/Windows. Em Linux/macOS, substitua curl.exe por curl."
            fullWidth
            multiline
            slotProps={{ input: { readOnly: true } }}
            onFocus={(event) => event.target.select()}
          />
        </div>
      ))}
      <Alert severity="info">
        A consulta entrega resumos agregados e retiradas de publicação. Preserve
        exportacao_id nas próximas páginas; o conjunto expira em cinco minutos.
        O envio automático à Agenda continua disponível na seção Serviços.
      </Alert>
    </section>
  );
}

export function CredentialManager({
  csrfToken,
  endpoint,
}: {
  csrfToken: string;
  endpoint: string;
}) {
  const query = useQuery({
    queryKey: ["integration-credentials"],
    queryFn: async () =>
      (await api.get<Credential[]>("/tecnologia/tokens")).data,
  });
  const [operation, setOperation] = useState<Operation | null>(null);
  const form = useForm<CredentialForm>({
    resolver: zodResolver(credentialSchema),
    defaultValues: { nome: "Agenda Digital", validade_dias: 90, password: "" },
  });
  const values = useWatch({ control: form.control });
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState("");
  // O segredo não passa pelo cache do React Query, storage, URL ou persistência do formulário.
  const [issued, setIssued] = useState<Issued | null>(null);

  useEffect(() => {
    if (!issued) return;
    const clear = () => setIssued(null);
    const timeout = window.setTimeout(clear, 120_000);
    window.addEventListener("pagehide", clear);
    return () => {
      window.clearTimeout(timeout);
      window.removeEventListener("pagehide", clear);
    };
  }, [issued]);

  function open(next: Operation) {
    form.reset({
      nome: next.credential?.nome || "Agenda Digital",
      validade_dias: next.credential?.expira_em === null ? null : 90,
      password: "",
    });
    setFailure("");
    setOperation(next);
  }

  function close() {
    if (pending) return;
    setOperation(null);
    form.resetField("password");
    setFailure("");
  }

  async function submit(data: CredentialForm) {
    if (!operation || pending) return;
    setPending(true);
    setFailure("");
    try {
      const path =
        operation.type === "criar"
          ? "/tecnologia/tokens"
          : `/tecnologia/tokens/${operation.credential!.id}/${operation.type}`;
      const body =
        operation.type === "revogar" ? { password: data.password } : data;
      const response = await api.post<Issued>(path, body, {
        headers: { "X-CSRF-Token": csrfToken },
      });
      if (operation.type !== "revogar") setIssued(response.data);
      setOperation(null);
      form.resetField("password");
      toast.success(
        operation.type === "revogar"
          ? "Token revogado."
          : "Token criado. Copie e guarde no servidor da Agenda.",
      );
      await query.refetch();
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      form.resetField("password");
      setPending(false);
    }
  }

  return (
    <section className="panel">
      <div className="page-heading">
        <div>
          <h2>Tokens de leitura para a Agenda</h2>
          <p className="muted">
            Escopo: acoes.resumos.read. Somente consultas agregadas; até 60
            requisições por minuto por token.
          </p>
        </div>
        <Button
          variant="contained"
          onClick={() => open({ type: "criar" })}
          disabled={query.isPending || query.isError}
        >
          Criar token
        </Button>
      </div>
      {query.isPending ? (
        <p role="status">Carregando tokens…</p>
      ) : query.isError ? (
        <Alert
          severity="error"
          action={
            <Button onClick={() => query.refetch()}>Tentar novamente</Button>
          }
        >
          {errorMessage(query.error)}
        </Alert>
      ) : !query.data.length ? (
        <p>
          Nenhum token criado. Crie uma credencial para a Agenda consultar os
          resumos.
        </p>
      ) : (
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Tokens de integração — tabela com rolagem"
        >
          <table className="data-table">
            <caption className="sr-only">
              Tokens de leitura da Agenda Digital
            </caption>
            <thead>
              <tr>
                <th>Nome / identificação</th>
                <th>Status</th>
                <th>Validade</th>
                <th>Último uso</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((credential) => (
                <tr key={credential.id}>
                  <td>
                    {credential.nome}
                    <br />
                    <code>{credential.token_mascarado}</code>
                  </td>
                  <td>
                    {
                      {
                        ativa: "Ativo",
                        expirada: "Expirado",
                        revogada: "Revogado",
                      }[credential.status]
                    }
                  </td>
                  <td>{expirationLabel(credential.expira_em)}</td>
                  <td>
                    {dateLabel(credential.ultimo_uso_em)}
                    <br />
                    {credential.chamadas} consultas
                  </td>
                  <td>
                    {credential.status === "ativa" && (
                      <Stack
                        direction="row"
                        useFlexGap
                        sx={{ flexWrap: "wrap", gap: 1 }}
                      >
                        <Button
                          aria-label={`Rotacionar token ${credential.nome}`}
                          onClick={() =>
                            open({ type: "rotacionar", credential })
                          }
                        >
                          Rotacionar
                        </Button>
                        <Button
                          aria-label={`Revogar token ${credential.nome}`}
                          onClick={() => open({ type: "revogar", credential })}
                        >
                          Revogar
                        </Button>
                      </Stack>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Dialog
        open={Boolean(operation)}
        onClose={close}
        fullWidth
        maxWidth="sm"
        aria-labelledby="credential-operation-title"
      >
        <form onSubmit={form.handleSubmit(submit)}>
          <DialogTitle id="credential-operation-title">
            {operation?.type === "revogar"
              ? "Revogar token"
              : operation?.type === "rotacionar"
                ? "Rotacionar token"
                : "Criar token para a Agenda"}
          </DialogTitle>
          <DialogContent>
            {failure && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {failure}
              </Alert>
            )}
            <Alert severity="info" sx={{ mb: 2 }}>
              {operation?.type === "revogar"
                ? "A credencial deixará de autorizar consultas após a confirmação."
                : operation?.type === "rotacionar"
                  ? "O token anterior será revogado na criação do substituto. Atualize a credencial no servidor da Agenda."
                  : "O token será exibido uma única vez por até dois minutos. Salve no gerenciador de segredos da Agenda."}
            </Alert>
            {operation?.type !== "revogar" && (
              <>
                <TextField
                  label="Nome do token"
                  {...form.register("nome")}
                  error={Boolean(form.formState.errors.nome)}
                  helperText={form.formState.errors.nome?.message}
                  required
                  fullWidth
                  margin="normal"
                  autoFocus
                  disabled={pending}
                  slotProps={{ htmlInput: { minLength: 3, maxLength: 80 } }}
                />
                <Controller
                  name="validade_dias"
                  control={form.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      value={field.value === null ? "nunca" : field.value}
                      label="Validade do token"
                      select
                      fullWidth
                      margin="normal"
                      disabled={pending}
                      onChange={(event) =>
                        field.onChange(
                          event.target.value === "nunca"
                            ? null
                            : Number(event.target.value),
                        )
                      }
                    >
                      <MenuItem value="nunca">Nunca expirar</MenuItem>
                      {[30, 90, 180, 365].map((value) => (
                        <MenuItem key={value} value={value}>
                          {value} dias
                        </MenuItem>
                      ))}
                    </TextField>
                  )}
                />
              </>
            )}
            <TextField
              label="Confirme sua senha institucional"
              type="password"
              autoComplete="current-password"
              {...form.register("password")}
              error={Boolean(form.formState.errors.password)}
              helperText={form.formState.errors.password?.message}
              required
              fullWidth
              margin="normal"
              autoFocus={operation?.type === "revogar"}
              disabled={pending}
              slotProps={{ htmlInput: { maxLength: 1024 } }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={close} disabled={pending}>
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={
                pending ||
                !values.password ||
                (operation?.type !== "revogar" &&
                  (values.nome?.trim().length || 0) < 3)
              }
            >
              {pending
                ? "Confirmando…"
                : operation?.type === "revogar"
                  ? "Confirmar revogação"
                  : "Gerar token"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      <Dialog
        open={Boolean(issued)}
        onClose={() => setIssued(null)}
        fullWidth
        maxWidth="md"
        aria-labelledby="issued-token-title"
      >
        <DialogTitle id="issued-token-title">
          Token criado — copie agora
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Esta é a única exibição do token, por até dois minutos. Depois de
            fechar, você poderá gerar um substituto. Guarde a credencial somente
            no servidor ou gerenciador de segredos da Agenda.
          </Alert>
          {issued && (
            <>
              <TextField
                label="Token de integração"
                value={issued.token}
                fullWidth
                slotProps={{
                  input: { readOnly: true },
                  htmlInput: { autoComplete: "off", spellCheck: false },
                }}
                onFocus={(event) => event.target.select()}
              />
              <Stack
                direction="row"
                useFlexGap
                sx={{ my: 2, flexWrap: "wrap", gap: 1 }}
              >
                <Button
                  variant="contained"
                  onClick={() => copyIntegrationText(issued.token)}
                >
                  Copiar token
                </Button>
                <Button
                  variant="outlined"
                  onClick={() =>
                    copyIntegrationText(curl(endpoint, issued.token))
                  }
                >
                  Copiar cURL com token
                </Button>
              </Stack>
              <p>
                Validade: {expirationLabel(issued.credencial.expira_em)}.
                Escopo: {issued.credencial.escopo}.
              </p>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIssued(null)}>
            Concluir e ocultar token
          </Button>
        </DialogActions>
      </Dialog>
    </section>
  );
}
