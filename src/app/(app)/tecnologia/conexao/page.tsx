"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Chip } from "@mui/material";
import { useSession } from "@/components/session-context";
import { api, dateLabel, errorMessage } from "@/lib/api";
type Health = {
  banco: string;
  latencia_ms: number;
  api: string;
  armazenamento: string;
  agenda: string;
  fila_pendente: number;
  ultima_confirmacao: string | null;
  verificado_em: string;
  credencial: { alias: string; escopo: string; status: string };
};
export default function ConnectionPage() {
  const session = useSession();
  const query = useQuery({
    queryKey: ["saude"],
    queryFn: async () => (await api.get<Health>("/tecnologia/saude")).data,
    enabled: session.equipe === "tecnologia",
  });
  const synchronize = useMutation({
    mutationFn: () =>
      api.post(
        "/tecnologia/sincronizar-agenda",
        {},
        { headers: { "X-CSRF-Token": session.csrf_token } },
      ),
    onSuccess: () => query.refetch(),
  });
  if (session.equipe !== "tecnologia")
    return (
      <Alert severity="error">
        Sem permissão. Esta página é exclusiva da equipe Tecnologia.
      </Alert>
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Conexão e integrações</h1>
          <p>Diagnóstico restrito da infraestrutura e do fluxo de resumos.</p>
        </div>
        <Button
          variant="outlined"
          onClick={() => query.refetch()}
          disabled={query.isFetching}
        >
          Verificar novamente
        </Button>
      </div>
      {synchronize.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorMessage(synchronize.error)}
        </Alert>
      )}
      {query.isPending ? (
        <div className="panel" role="status">
          Verificando serviços…
        </div>
      ) : query.isError ? (
        <Alert severity="error">{errorMessage(query.error)}</Alert>
      ) : (
        <>
          <section className="panel">
            <h2>Serviços</h2>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Componente</th>
                    <th>Situação</th>
                    <th>Informação</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>PostgreSQL institucional</td>
                    <td>
                      <Chip label={query.data.banco} variant="outlined" />
                    </td>
                    <td>{query.data.latencia_ms} ms</td>
                  </tr>
                  <tr>
                    <td>API FastAPI</td>
                    <td>{query.data.api}</td>
                    <td>Verificação de disponibilidade</td>
                  </tr>
                  <tr>
                    <td>Armazenamento do módulo</td>
                    <td>{query.data.armazenamento}</td>
                    <td>Persistência isolada do módulo</td>
                  </tr>
                  <tr>
                    <td>Agenda Digital</td>
                    <td>{query.data.agenda}</td>
                    <td>{query.data.fila_pendente} resumos na fila</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="muted">
              Última confirmação: {dateLabel(query.data.ultima_confirmacao)}.
              Verificado em {dateLabel(query.data.verificado_em)}.
            </p>
            <Button
              onClick={() => synchronize.mutate()}
              disabled={
                synchronize.isPending ||
                query.data.credencial.status !== "configurada"
              }
            >
              {synchronize.isPending
                ? "Sincronizando…"
                : "Sincronizar resumos com a Agenda"}
            </Button>
          </section>
          <section className="panel">
            <h2>Credencial de integração</h2>
            <p>
              Alias: <strong>{query.data.credencial.alias}</strong>
            </p>
            <p>Escopo: {query.data.credencial.escopo}</p>
            <p>Status: {query.data.credencial.status}</p>
            <Alert severity="info">
              Provisionamento e rotação devem ocorrer pelo gerenciador
              institucional de segredos. O recebimento só é confirmado após o
              reconhecimento do evento pela Agenda.
            </Alert>
          </section>
        </>
      )}
    </>
  );
}
