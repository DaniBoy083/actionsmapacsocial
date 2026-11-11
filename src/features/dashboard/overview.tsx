"use client";
import Link from "next/link";
import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Alert, Button, MenuItem, TextField } from "@mui/material";
import {
  FiActivity,
  FiArrowRight,
  FiCheckCircle,
  FiMapPin,
  FiUsers,
} from "react-icons/fi";
import {
  api,
  dateLabel,
  errorMessage,
  type Indicators,
  type Municipality,
} from "@/lib/api";
import { useSession } from "@/components/session-context";
import {
  emptyInstitutionalFilters,
  InstitutionalFilters,
} from "@/features/actions/institutional-filters";

const emptyFilters = {
  ...emptyInstitutionalFilters,
  acao: "",
  municipio: "",
  local: "",
  inicio: "",
  fim: "",
};

export function Overview() {
  const session = useSession();
  const [draft, setDraft] = useState(emptyFilters);
  const [filters, setFilters] = useState(emptyFilters);
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  const query = useQuery({
    queryKey: ["indicadores", filters],
    placeholderData: keepPreviousData,
    queryFn: async () =>
      (
        await api.get<Indicators>("/indicadores", {
          params: Object.fromEntries(
            Object.entries(filters).filter(([, value]) => value !== ""),
          ),
        })
      ).data,
  });
  if (query.isPending)
    return (
      <section className="panel" role="status">
        Carregando indicadores…
      </section>
    );
  const data = query.data;
  const stats = data
    ? [
        { label: "Ações institucionais", value: data.acoes, icon: FiActivity },
        {
          label: "Registros de participação",
          value: data.participacoes,
          icon: FiUsers,
        },
        {
          label: "Municípios alcançados",
          value: data.municipios,
          icon: FiMapPin,
        },
        {
          label: "Ações em revisão",
          value: data.em_revisao,
          icon: FiCheckCircle,
        },
      ]
    : [];
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
      <section className="panel">
        <details>
          <summary>Filtrar indicadores</summary>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setFilters({ ...draft });
            }}
          >
            <div className="filter-extra">
              <TextField
                label="Código da ação"
                value={draft.acao}
                onChange={(event) =>
                  setDraft({ ...draft, acao: event.target.value })
                }
                slotProps={{ htmlInput: { maxLength: 36 } }}
              />
              <TextField
                select
                label="Município do evento"
                value={draft.municipio}
                onChange={(event) =>
                  setDraft({ ...draft, municipio: event.target.value })
                }
              >
                <MenuItem value="">Todos</MenuItem>
                {municipalities.data?.map((place) => (
                  <MenuItem key={place.codigo} value={place.codigo}>
                    {place.nome}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Local do evento"
                value={draft.local}
                onChange={(event) =>
                  setDraft({ ...draft, local: event.target.value })
                }
                slotProps={{ htmlInput: { maxLength: 160 } }}
              />
              <TextField
                label="Início da ação a partir de"
                type="date"
                value={draft.inicio}
                onChange={(event) =>
                  setDraft({ ...draft, inicio: event.target.value })
                }
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                label="Início da ação até"
                type="date"
                value={draft.fim}
                onChange={(event) =>
                  setDraft({ ...draft, fim: event.target.value })
                }
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </div>
            <InstitutionalFilters
              value={draft}
              onChange={(key, value) => setDraft({ ...draft, [key]: value })}
            />
            <div className="actions-row">
              <Button variant="contained" type="submit">
                Aplicar filtros
              </Button>
              <Button
                onClick={() => {
                  setDraft(emptyFilters);
                  setFilters(emptyFilters);
                }}
              >
                Limpar filtros
              </Button>
            </div>
          </form>
        </details>
      </section>
      {query.isError && (
        <Alert severity="error">
          {errorMessage(query.error)}{" "}
          <Button onClick={() => query.refetch()}>Tentar novamente</Button>
        </Alert>
      )}
      {query.isFetching && <p role="status">Atualizando indicadores…</p>}
      <div className="stat-grid">
        {stats.map((item) => (
          <article className="stat-card" key={item.label}>
            <item.icon />
            <strong>{item.value.toLocaleString("pt-BR")}</strong>
            <span>{item.label}</span>
          </article>
        ))}
      </div>
      {data && (
        <section className="panel">
          <div
            className="eyebrow"
            style={{ color: "#b80d27", marginBottom: 12 }}
          >
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
            Escopo: {data.escopo}. Atualizado em {dateLabel(data.atualizado_em)}
            . Participações representam registros, sem estimativa automática de
            pessoas únicas.
          </p>
          <p className="muted">
            Cadastros distintos no recorte: {data.cadastros_distintos}.
            Identificadores internos não comprovam pessoas únicas entre ações;
            não há conciliação automática por nome ou CPF. Participações sem
            local nas ações selecionadas: {data.participacoes_sem_local};
            excluídas dos totais ao filtrar município/local. Ações sem
            instrumento identificado: {data.acoes_sem_instrumento}.
          </p>
        </section>
      )}
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
