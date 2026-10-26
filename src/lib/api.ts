import axios from "axios";
export const api = axios.create({
  baseURL: "/api/backend",
  timeout: 30_000,
  withCredentials: true,
});
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401)
      return "Sua sessão expirou. Entre novamente.";
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Não foi possível concluir. Verifique a conexão e tente novamente.";
}
export type Session = {
  profissional_id: string;
  nome: string;
  tipo_login: string;
  equipe: "administracao" | "tecnologia";
  csrf_token: string;
  agenda_url: string;
};
export type Location = {
  municipio_ibge: string;
  municipio_nome?: string;
  nome_local: string;
};
export type Action = {
  id: string;
  versao: number;
  nome: string;
  categoria: string;
  descricao: string;
  resumo_publico: string;
  inicio_em: string | null;
  fim_em: string | null;
  status: string;
  locais: Location[];
  beneficiarios: number;
  atualizado_em: string;
  historico?: { operacao: string; criado_em: string }[];
};
export type Municipality = { codigo: string; nome: string };
export type Indicators = {
  acoes: number;
  participacoes: number;
  municipios: number;
  em_revisao: number;
  por_municipio: { codigo: string; nome: string; acoes: number }[];
  atualizado_em: string;
  escopo: string;
};
export function dateLabel(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Fortaleza",
      }).format(
        new Date(value.length === 10 ? value + "T12:00:00-03:00" : value),
      )
    : "Não informada";
}
export const statusLabels: Record<string, string> = {
  rascunho: "Rascunho",
  em_revisao: "Em revisão",
  validada: "Validada",
  publicada: "Publicada",
  arquivada: "Arquivada",
};
