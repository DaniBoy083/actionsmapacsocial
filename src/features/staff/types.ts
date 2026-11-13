import axios from "axios";
import { errorMessage } from "@/lib/api";

export const staffCategories = {
  MEDICO: "Oftalmologista",
  OPTOMETRISTA: "Optometrista",
  RECEPCAO: "Recepcionista",
};
export const states =
  "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(
    " ",
  );
export type StaffData = {
  identidade_institucional_id: string | null;
  registro_clinico_autorizado: boolean;
  autorizacao_clinica_referencia: string;
  nome: string;
  categoria: keyof typeof staffCategories;
  registro_conselho: string | null;
  registro_numero: string | null;
  registro_uf: string | null;
  rqe: string | null;
  habilitacao_validada: boolean;
  habilitacao_referencia: string;
  ativo: boolean;
  divulgacao_autorizada: boolean;
  divulgacao_referencia: string;
};
export type Staff = StaffData & {
  id: string;
  versao: number;
  atualizado_em: string;
  conferido_por: string | null;
  conferido_em: string | null;
  divulgacao_registrada_por: string | null;
  divulgacao_registrada_em: string | null;
};
export type Assignment = {
  conta_operacional_ativa?: boolean;
  id: string;
  versao: number;
  acao_id: string;
  profissional_id: string;
  profissional: Staff;
  profissional_snapshot: Staff;
  papel: "PROFISSIONAL" | "RECEPCAO";
  ativo: boolean;
  locais_indices: number[] | null;
  locais_snapshot:
    { indice: number; municipio_ibge: string; nome_local: string }[] | null;
  atualizado_em: string;
};
export type PageResult<T> = {
  items: T[];
  total: number;
  pagina: number;
  tamanho: number;
};
export function staffPayload(staff?: Staff): StaffData {
  return {
    identidade_institucional_id: staff?.identidade_institucional_id ?? null,
    registro_clinico_autorizado: staff?.registro_clinico_autorizado ?? false,
    autorizacao_clinica_referencia: staff?.autorizacao_clinica_referencia ?? "",
    nome: staff?.nome ?? "",
    categoria: staff?.categoria ?? "RECEPCAO",
    registro_conselho: staff?.registro_conselho ?? null,
    registro_numero: staff?.registro_numero ?? null,
    registro_uf: staff?.registro_uf ?? null,
    rqe: staff?.rqe ?? null,
    habilitacao_validada: staff?.habilitacao_validada ?? false,
    habilitacao_referencia: staff?.habilitacao_referencia ?? "",
    ativo: staff?.ativo ?? true,
    divulgacao_autorizada: staff?.divulgacao_autorizada ?? false,
    divulgacao_referencia: staff?.divulgacao_referencia ?? "",
  };
}
export function staffError(error: unknown): string {
  if (axios.isAxiosError(error) && error.response?.status === 422) {
    const fields = error.response.data?.campos;
    if (Array.isArray(fields)) {
      const messages = fields
        .map((field) =>
          typeof field.mensagem === "string"
            ? field.mensagem.replace(/^Value error, /, "")
            : "",
        )
        .filter(Boolean);
      if (messages.length) return [...new Set(messages)].join(" ");
    }
  }
  return errorMessage(error);
}
