"use client";

import Image from "next/image";
import { instrumentLabels, type Institutional } from "./institutional";

export function InstitutionalSummary({
  actionId,
  value,
  onImageLoad,
  onImageError,
}: {
  actionId: string;
  value: Institutional;
  onImageLoad?: (source: string) => void;
  onImageError?: () => void;
}) {
  const instrument = value.instrumento;
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
  ];
  return (
    <div className="institutional-summary">
      <div className="institutional-logos">
        {images.map(({ source, alt }) => (
          <Image
            key={source}
            unoptimized
            src={source}
            alt={alt}
            width={120}
            height={80}
            style={{ objectFit: "contain", maxWidth: "100%" }}
            onLoad={() => onImageLoad?.(source)}
            onError={onImageError}
          />
        ))}
      </div>
      <dl className="institutional-details">
        <div>
          <dt>Apoio</dt>
          <dd>
            {value.apoio === "TOTAL"
              ? "Total"
              : value.apoio === "PARCIAL"
                ? "Parcial"
                : "Não informado"}
          </dd>
        </div>
        <div>
          <dt>Instrumento</dt>
          <dd>{instrumentLabels[instrument.tipo]}</dd>
        </div>
        <div>
          <dt>Nome/título da emenda ou convênio</dt>
          <dd>{instrument.nome || "Não informado"}</dd>
        </div>
        <div>
          <dt>Número da emenda/convênio</dt>
          <dd>{instrument.numero || "Não informado"}</dd>
        </div>
        <div>
          <dt>Autor da emenda</dt>
          <dd>{instrument.autor || "Não informado / não se aplica"}</dd>
        </div>
        <div>
          <dt>Órgão governamental</dt>
          <dd>{value.governo.nome || "Não informado"}</dd>
        </div>
        <div>
          <dt>Clínica parceira</dt>
          <dd>{value.clinica.nome || "Não informada"}</dd>
        </div>
      </dl>
    </div>
  );
}
