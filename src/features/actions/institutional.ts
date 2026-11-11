import { z } from "zod";

const brandSchema = z
  .object({
    nome: z.string().trim().max(160),
    uso_autorizado: z.boolean(),
    divulgacao_autorizada: z.boolean(),
    logo_id: z.string().nullable(),
    conteudo_base64: z.string().max(349528).nullable().optional(),
  })
  .superRefine((brand, ctx) => {
    if (
      (brand.logo_id || brand.conteudo_base64 || brand.divulgacao_autorizada) &&
      (!brand.nome || !brand.uso_autorizado)
    )
      ctx.addIssue({
        code: "custom",
        message: "Informe o parceiro e autorize o uso da marca.",
      });
  });

export const institutionalSchema = z
  .object({
    apoio: z.enum(["TOTAL", "PARCIAL"]).nullable(),
    instrumento: z.object({
      tipo: z.enum(["EMENDA", "CONVENIO", "OUTRO", "NAO_INFORMADO"]),
      nome: z.string().trim().max(160),
      numero: z.string().trim().max(80),
      autor: z.string().trim().max(160),
      divulgacao_autorizada: z.boolean(),
    }),
    governo: brandSchema,
    clinica: brandSchema,
  })
  .superRefine(({ instrumento }, ctx) => {
    if (
      instrumento.tipo === "NAO_INFORMADO" &&
      (instrumento.nome ||
        instrumento.numero ||
        instrumento.autor ||
        instrumento.divulgacao_autorizada)
    )
      ctx.addIssue({
        code: "custom",
        message:
          "Selecione o tipo do instrumento ou deixe seus dados em branco.",
      });
    if (instrumento.divulgacao_autorizada && !instrumento.nome)
      ctx.addIssue({
        code: "custom",
        message:
          "Informe o nome do instrumento antes de autorizar a divulgação.",
      });
  });

export type Institutional = z.infer<typeof institutionalSchema>;
export const emptyInstitutional = (): Institutional => ({
  apoio: null,
  instrumento: {
    tipo: "NAO_INFORMADO",
    nome: "",
    numero: "",
    autor: "",
    divulgacao_autorizada: false,
  },
  governo: {
    nome: "",
    uso_autorizado: false,
    divulgacao_autorizada: false,
    logo_id: null,
  },
  clinica: {
    nome: "",
    uso_autorizado: false,
    divulgacao_autorizada: false,
    logo_id: null,
  },
});

export const instrumentLabels: Record<
  Institutional["instrumento"]["tipo"],
  string
> = {
  EMENDA: "Emenda",
  CONVENIO: "Convênio",
  OUTRO: "Outro",
  NAO_INFORMADO: "Não informado",
};
