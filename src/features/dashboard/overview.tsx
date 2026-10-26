"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button } from "@mui/material";
import {
  FiActivity,
  FiArrowRight,
  FiCheckCircle,
  FiMapPin,
  FiUsers,
} from "react-icons/fi";
import { api, dateLabel, errorMessage, type Indicators } from "@/lib/api";
import { useSession } from "@/components/session-context";

export function Overview() {
  const session = useSession();
  const query = useQuery({
    queryKey: ["indicadores"],
    queryFn: async () => (await api.get<Indicators>("/indicadores")).data,
  });
  if (query.isPending)
    return (
      <section className="panel" role="status">
        Carregando indicadores…
      </section>
    );
  if (query.isError)
    return (
      <Alert severity="error">
        {errorMessage(query.error)}{" "}
        <Button onClick={() => query.refetch()}>Tentar novamente</Button>
      </Alert>
    );
  const data = query.data;
  const stats = [
    { label: "Ações institucionais", value: data.acoes, icon: FiActivity },
    {
      label: "Registros de participação",
      value: data.participacoes,
      icon: FiUsers,
    },
    { label: "Municípios alcançados", value: data.municipios, icon: FiMapPin },
    { label: "Ações em revisão", value: data.em_revisao, icon: FiCheckCircle },
  ];
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{`Olá, ${session.nome.split(" ")[0]}`}</h1>
          <p>Uma visão das iniciativas e do alcance da AC Social na Paraíba.</p>
        </div>
        <Button
          component={Link}
          href="/acoes"
          variant="contained"
          endIcon={<FiArrowRight />}
        >
          Gerenciar ações
        </Button>
      </div>
      <div className="stat-grid">
        {stats.map((item) => (
          <article className="stat-card" key={item.label}>
            <item.icon />
            <strong>{item.value.toLocaleString("pt-BR")}</strong>
            <span>{item.label}</span>
          </article>
        ))}
      </div>
      <section className="panel">
        <div className="eyebrow" style={{ color: "#b80d27", marginBottom: 12 }}>
          Presença na Paraíba
        </div>
        <h2>Ações por município</h2>
        <p className="muted">
          Cada ação conta uma vez no total global e uma vez em cada município
          onde ocorreu. A soma municipal pode superar o total de ações.
        </p>
        {!data.por_municipio.length ? (
          <div className="empty-state">
            <FiMapPin />
            <h2>O alcance começa com uma ação</h2>
            <p className="muted">
              Os municípios aparecerão aqui após o primeiro cadastro.
            </p>
            <Button component={Link} href="/acoes" variant="outlined">
              Cadastrar uma ação
            </Button>
          </div>
        ) : (
          data.por_municipio.map((row) => (
            <div className="bar-row" key={row.codigo}>
              <span>{row.nome}</span>
              <div className="bar-track" aria-hidden="true">
                <div
                  style={{
                    width: `${(row.acoes / Math.max(1, data.acoes)) * 100}%`,
                  }}
                />
              </div>
              <strong>{row.acoes}</strong>
            </div>
          ))
        )}
        <p className="muted">
          Escopo: {data.escopo}. Atualizado em {dateLabel(data.atualizado_em)}.
          Participações representam registros, sem estimativa automática de
          pessoas únicas.
        </p>
      </section>
      <section className="panel">
        <h2>Integração institucional</h2>
        <p className="muted">
          Somente resumos gerais seguem para revisão e publicação pelo fluxo
          institucional.
        </p>
        <div className="pipeline">
          <span>AC Actions Map</span>→<span>Agenda Digital</span>→
          <span>Plataforma de Dados</span>→<span>Portal Institucional</span>
        </div>
      </section>
    </>
  );
}
