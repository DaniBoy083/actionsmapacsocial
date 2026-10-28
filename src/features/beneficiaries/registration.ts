import { z } from "zod";

const optionalDate = z.iso.date("Informe uma data válida.").or(z.literal(""));
const municipality = z
  .string()
  .regex(/^25\d{5}$/)
  .or(z.literal(""));
const digits = (value: string) => value.replace(/\D/g, "");
function validCpf(value: string) {
  if (!value) return true;
  if (!/^[0-9.\- ]+$/.test(value)) return false;
  const cpf = digits(value);
  if (cpf.length !== 11 || new Set(cpf).size === 1) return false;
  return [9, 10].every((size) => {
    const sum = [...cpf.slice(0, size)].reduce(
      (total, digit, index) => total + Number(digit) * (size + 1 - index),
      0,
    );
    return ((sum * 10) % 11) % 10 === Number(cpf[size]);
  });
}
export const registrationSchema = z
  .object({
    nome: z.string().trim().min(2, "Informe o nome.").max(160),
    cpf: z
      .string()
      .trim()
      .max(14)
      .refine(validCpf, "Informe um CPF válido ou deixe em branco."),
    cpf_documento: z
      .string()
      .trim()
      .max(14)
      .refine(
        (value) =>
          !value || (/^[0-9.\- ]+$/.test(value) && digits(value).length === 11),
        "Transcreva os 11 dígitos legíveis ou deixe em branco.",
      ),
    telefone: z
      .string()
      .trim()
      .max(24)
      .refine((value) => {
        if (!value) return true;
        if (!/^[+0-9() .\-]+$/.test(value)) return false;
        let phone = digits(value);
        if ([12, 13].includes(phone.length) && phone.startsWith("55"))
          phone = phone.slice(2);
        return phone.length >= 7 && phone.length <= 13;
      }, "Transcreva o telefone informado, sem inventar DDD."),
    data_nascimento: optionalDate.refine(
      (value) => !value || value <= new Date().toISOString().slice(0, 10),
      "Nascimento não pode estar no futuro.",
    ),
    data_ficha: optionalDate,
    municipio_ficha_ibge: municipality,
    municipio_residencia_ibge: municipality,
    responsavel: z.string().trim().max(160),
    observacoes: z.string().trim().max(1000),
    recebimento_confirmado: z.enum(["", "sim", "nao"]),
    local_indice: z.string().regex(/^\d*$/),
  })
  .refine(
    (value) =>
      !value.data_nascimento ||
      !value.data_ficha ||
      value.data_nascimento <= value.data_ficha,
    {
      message: "A ficha não pode ser anterior ao nascimento.",
      path: ["data_ficha"],
    },
  );
export type RegistrationForm = z.infer<typeof registrationSchema>;
export const emptyRegistration: RegistrationForm = {
  nome: "",
  cpf: "",
  cpf_documento: "",
  telefone: "",
  data_nascimento: "",
  data_ficha: "",
  municipio_ficha_ibge: "",
  municipio_residencia_ibge: "",
  responsavel: "",
  observacoes: "",
  recebimento_confirmado: "",
  local_indice: "",
};
export type BeneficiaryData = {
  nome: string;
  cpf: string | null;
  cpf_documento: string | null;
  telefone: string | null;
  data_nascimento: string | null;
  data_ficha: string | null;
  municipio_ficha_ibge: string | null;
  municipio_residencia_ibge: string | null;
  responsavel: string | null;
  observacoes: string | null;
  recebimento_confirmado: boolean | null;
  local_indice: number | null;
};
export type BeneficiarySheet = BeneficiaryData & {
  id: string;
  versao: number;
  acao: { id: string; nome: string };
  municipio_ficha_nome: string | null;
  municipio_residencia_nome: string | null;
  segunda_via: boolean;
  emitido_em: string | null;
};
export function registrationValues(
  data?: Partial<BeneficiaryData>,
): RegistrationForm {
  return Object.fromEntries(
    Object.keys(emptyRegistration).map((key) => {
      const field = key as keyof RegistrationForm;
      const value = data?.[field];
      return [
        field,
        field === "recebimento_confirmado"
          ? value === true
            ? "sim"
            : value === false
              ? "nao"
              : ""
          : value == null
            ? ""
            : String(value),
      ];
    }),
  ) as RegistrationForm;
}
export function registrationPayload(values: RegistrationForm): BeneficiaryData {
  return {
    ...values,
    cpf: values.cpf || null,
    cpf_documento: values.cpf_documento || null,
    telefone: values.telefone || null,
    data_nascimento: values.data_nascimento || null,
    data_ficha: values.data_ficha || null,
    municipio_ficha_ibge: values.municipio_ficha_ibge || null,
    municipio_residencia_ibge: values.municipio_residencia_ibge || null,
    responsavel: values.responsavel || null,
    observacoes: values.observacoes || null,
    recebimento_confirmado:
      values.recebimento_confirmado === ""
        ? null
        : values.recebimento_confirmado === "sim",
    local_indice:
      values.local_indice === "" ? null : Number(values.local_indice),
  };
}
