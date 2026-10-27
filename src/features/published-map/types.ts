import { z } from "zod";

const count = z.number().int().nonnegative().max(Number.MAX_SAFE_INTEGER);
const totals = z
  .object({
    action_count: count,
    participation_count: count,
    people_count: count,
  })
  .strict();
export const mapSchema = z
  .object({
    status: z.enum([
      "available",
      "empty",
      "unavailable",
      "not_configured",
      "unauthorized",
      "contract_unavailable",
    ]),
    checked_at: z.iso.datetime({ offset: true }),
    refresh_after_seconds: z.number().int().min(1).max(86400),
    generation: z
      .string()
      .regex(/^[1-9][0-9]{0,18}$/)
      .nullable(),
    captured_at: z.iso.datetime({ offset: true }).nullable(),
    expires_at: z.iso.datetime({ offset: true }).nullable(),
    summary: totals
      .extend({
        municipality_count: count.max(223),
        undated_action_count: count,
        unallocated: totals,
      })
      .strict()
      .nullable(),
    municipalities: z
      .array(
        z
          .object({
            code: z.string().regex(/^25[0-9]{5}$/),
            name: z.string().max(200),
            action_count: count,
            unallocated_action_count: count,
            single_municipality_participations: count,
            single_municipality_people: count,
          })
          .strict(),
      )
      .max(223),
  })
  .strict();
export type PublishedMap = z.infer<typeof mapSchema>;

export function captureLabel(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo",
  }).format(new Date(value));
}

export function searchText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}
