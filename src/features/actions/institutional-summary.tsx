"use client";

import Image from "next/image";
import {
  institutionalImages,
  instrumentLabels,
  institutionTypes,
  type Institutional,
} from "./institutional";

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
  const images = institutionalImages(actionId, value);
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
        {(["contratantes", "apoiadores"] as const).map((role) => (
          <div key={role}>
            <dt>{role === "contratantes" ? "Contratantes" : "Apoiadores"}</dt>
            <dd>
              {value[role]?.length ? (
                <ul>
                  {value[role].map((link, index) => (
                    <li key={index}>
                      {link.nome} · {institutionTypes[link.tipo]}
                      {link.modalidade
                        ? ` · apoio ${link.modalidade === "TOTAL" ? "total" : "parcial"}`
                        : ""}
                    </li>
                  ))}
                </ul>
              ) : (
                "Legado pendente de revisão dos papéis"
              )}
            </dd>
          </div>
        ))}
        {value.apoio && (
          <div>
            <dt>Apoio (cadastro anterior)</dt>
            <dd>
              {value.apoio === "TOTAL"
                ? "Total"
                : value.apoio === "PARCIAL"
                  ? "Parcial"
                  : "Não informado"}
            </dd>
          </div>
        )}
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
        {value.governo.nome && (
          <div>
            <dt>Órgão governamental</dt>
            <dd>{value.governo.nome || "Não informado"}</dd>
          </div>
        )}
        {value.clinica.nome && (
          <div>
            <dt>Clínica parceira</dt>
            <dd>{value.clinica.nome || "Não informada"}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
