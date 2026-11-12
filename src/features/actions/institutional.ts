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

export const institutionTypes = {
  ORGAO_GOVERNAMENTAL: "Órgão governamental",
  CLINICA: "Clínica",
  ORGANIZACAO_EMPRESA: "Organização/empresa",
  OUTRO: "Outro",
};
export const institutionLinkSchema = brandSchema.safeExtend({
  instituicao_id: z.string().uuid().nullable(),
  nome: z.string().trim().min(2, "Informe a instituição.").max(160),
  tipo: z.enum([
    "ORGAO_GOVERNAMENTAL",
    "CLINICA",
    "ORGANIZACAO_EMPRESA",
    "OUTRO",
  ]),
  modalidade: z.enum(["TOTAL", "PARCIAL"]).nullable(),
});
export type InstitutionLink = z.infer<typeof institutionLinkSchema>;
export const emptyLink = (): InstitutionLink => ({
  instituicao_id: null,
  nome: "",
  tipo: "OUTRO",
  modalidade: null,
  uso_autorizado: false,
  divulgacao_autorizada: false,
  logo_id: null,
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
    contratantes: z.array(institutionLinkSchema).min(1).max(100),
    apoiadores: z.array(institutionLinkSchema).min(1).max(100),
  })
  .superRefine(({ instrumento, contratantes, apoiadores }, ctx) => {
    if (
      apoiadores.some((item) => !item.modalidade) ||
      contratantes.some((item) => item.modalidade)
    )
      ctx.addIssue({
        code: "custom",
        message: "Informe a modalidade de cada apoiador.",
      });
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
  contratantes: [emptyLink()],
  apoiadores: [emptyLink()],
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

export function institutionalImages(actionId: string, value: Institutional) {
  const images = [
    { source: "/logo-ac-social.png", alt: "AC Social" },
    ...(["governo", "clinica"] as const).flatMap((slot) => {
      const brand = value[slot];
      return brand.logo_id && brand.uso_autorizado
        ? [
            {
              source: `/api/backend/acoes/${actionId}/marcas/${brand.logo_id}`,
              alt: brand.nome,
            },
          ]
        : [];
    }),
    ...[...(value.contratantes || []), ...(value.apoiadores || [])].flatMap(
      (link) =>
        link.logo_id && link.instituicao_id && link.uso_autorizado
          ? [
              {
                source: `/api/backend/instituicoes/${link.instituicao_id}/marcas/${link.logo_id}`,
                alt: link.nome,
              },
            ]
          : [],
    ),
  ];
  return images.filter(
    (item, index) =>
      images.findIndex((other) => other.source === item.source) === index,
  );
}
