"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  LinearProgress,
  MenuItem,
  Pagination,
  TextField,
} from "@mui/material";
import { FiRefreshCw } from "react-icons/fi";
import { api } from "@/lib/api";
import geography from "@/data/paraiba-map.json";
import { captureLabel, mapSchema, searchText } from "./types";
import "./published-map.css";

const messages: Record<string, string> = {
  not_configured:
    "A consulta à Plataforma Consolidada ainda não foi configurada. Procure a equipe de Tecnologia.",
  unauthorized:
    "A Plataforma Consolidada recusou o acesso. A equipe de Tecnologia precisa revisar a integração.",
  contract_unavailable:
    "A Plataforma Consolidada ainda não disponibilizou o contrato municipal esperado.",
  unavailable:
    "Não foi possível atualizar o mapa. Tente novamente em instantes.",
};
const number = (value: number) => value.toLocaleString("pt-BR");

export function PublishedActionsMap() {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState("");
  const [page, setPage] = useState(1);
  const [now, setNow] = useState(() => Date.now());
  const generation = useRef<bigint | null>(null);
  const content = useRef<string | null>(null);
  const query = useQuery({
    queryKey: ["published-map"],
    queryFn: async ({ signal }) => {
      const response = await api.get("/mapa-acoes", {
        signal,
        timeout: 25_000,
      });
      const data = mapSchema.parse(response.data);
      if (data.status === "available" || data.status === "empty") {
        if (
          !data.generation ||
          !data.summary ||
          !data.captured_at ||
          !data.expires_at ||
          Date.parse(data.expires_at) <= Date.now()
        )
          throw new Error("Projeção expirada.");
        const next = BigInt(data.generation);
        const fingerprint = JSON.stringify([data.summary, data.municipalities]);
        if (
          generation.current !== null &&
          (next < generation.current ||
            (next === generation.current && content.current !== fingerprint))
        )
          throw new Error("Geração antiga ou conflitante.");
        generation.current = next;
        content.current = fingerprint;
      }
      setNow(Date.now());
      return data;
    },
    staleTime: 0,
    gcTime: 0,
    retry: false,
    refetchOnWindowFocus: true,
    refetchInterval: (state) =>
      (state.state.status === "error"
        ? 30
        : (state.state.data?.refresh_after_seconds ?? 30)) * 1000,
  });
  const expires = query.data?.expires_at;
  useEffect(() => {
    if (!expires) return;
    const update = () => setNow(Date.now());
    const timer = setTimeout(
      update,
      Math.max(0, Date.parse(expires) - Date.now()) + 10,
    );
    document.addEventListener("visibilitychange", update);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", update);
    };
  }, [expires]);
  const data = query.data;
  const valid =
    !query.isError &&
    data &&
    ["available", "empty"].includes(data.status) &&
    data.expires_at &&
    Date.parse(data.expires_at) > now;
  const rows = useMemo(() => data?.municipalities ?? [], [data]);
  const byCode = useMemo(
    () => new Map(rows.map((row) => [row.code, row])),
    [rows],
  );
  const filtered = rows.filter((row) =>
    searchText(row.name).includes(searchText(search)),
  );
  const currentPage = Math.min(
    page,
    Math.max(1, Math.ceil(filtered.length / 5)),
  );
  const visible = filtered.slice((currentPage - 1) * 5, currentPage * 5);
  const city = byCode.get(selected);
  function selectCity(code: string) {
    setSelected(code);
    document.getElementById("municipality-details")?.focus();
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">Publicação institucional</div>
          <h1>Mapa de ações</h1>
          <p className="muted">
            Ações publicadas na origem, consultadas na Plataforma Consolidada de
            Análise de Dados.
          </p>
        </div>
        <Button
          variant="outlined"
          startIcon={<FiRefreshCw />}
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
        >
          Atualizar mapa
        </Button>
      </div>
      {query.isFetching && <LinearProgress aria-label="Atualizando mapa" />}
      {query.isPending ? (
        <section className="panel" role="status">
          Carregando mapa de ações…
        </section>
      ) : !valid || !data?.summary ? (
        <Alert severity="warning" role="status">
          {data?.expires_at && Date.parse(data.expires_at) <= now
            ? "A validade dos dados terminou. Atualize o mapa para consultar uma versão válida."
            : (messages[data?.status ?? "unavailable"] ?? messages.unavailable)}
          {data && (
            <span> Última consulta: {captureLabel(data.checked_at)}.</span>
          )}
        </Alert>
      ) : (
        <>
          <div className="stat-grid" aria-label="Totais globais da Plataforma">
            {[
              ["Ações", data.summary.action_count],
              ["Participações", data.summary.participation_count],
              ["Pessoas contempladas nas ações", data.summary.people_count],
              ["Municípios", data.summary.municipality_count],
            ].map(([label, value]) => (
              <article className="stat-card" key={label}>
                <strong>{number(Number(value))}</strong>
                <span>{label}</span>
              </article>
            ))}
          </div>
          <p className="muted">
            Fonte: Plataforma Consolidada. Captura:{" "}
            {captureLabel(data.captured_at!)} (Brasília). Válido até{" "}
            {captureLabel(data.expires_at!)}. Atualização periódica, sujeita à
            disponibilidade da fonte.
          </p>
          {data.status === "empty" ? (
            <Alert severity="info" role="status">
              A exportação válida não contém ações publicadas.
            </Alert>
          ) : (
            <>
              <section className="panel" aria-labelledby="map-title">
                <h2 id="map-title">Presença nos municípios da Paraíba</h2>
                <p id="map-description" className="muted">
                  As cores indicam ações que incluem cada município. Use a
                  seleção ou a tabela para consultar os detalhes. A soma
                  municipal pode superar o total global.
                </p>
                <div
                  className="published-map-legend"
                  aria-label="Legenda do mapa"
                >
                  {[
                    ["#fff8f9", "Sem ações nesta exportação"],
                    ["#f5a8b4", "1 ação"],
                    ["#b80d27", "2 a 4 ações"],
                    ["#65111f", "5 ou mais ações"],
                  ].map(([color, label]) => (
                    <span key={label}>
                      <i style={{ backgroundColor: color }} />
                      {label}
                    </span>
                  ))}
                </div>
                <svg
                  className="published-map-geometry"
                  viewBox={geography.viewBox}
                  role="group"
                  aria-labelledby="map-title"
                  aria-describedby="map-description"
                >
                  {geography.municipalities.map((municipality) => {
                    const amount =
                      byCode.get(municipality.id)?.action_count ?? 0;
                    return (
                      <path
                        key={municipality.id}
                        d={municipality.path}
                        role="button"
                        tabIndex={amount ? 0 : -1}
                        aria-label={`${municipality.name}: ${amount} ações nesta exportação`}
                        aria-pressed={selected === municipality.id}
                        fill={
                          amount >= 5
                            ? "#65111f"
                            : amount >= 2
                              ? "#b80d27"
                              : amount
                                ? "#f5a8b4"
                                : "#fff8f9"
                        }
                        stroke="#65111f"
                        strokeWidth={selected === municipality.id ? 3 : 0.6}
                        onClick={() => selectCity(municipality.id)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            selectCity(municipality.id);
                          }
                        }}
                      >
                        <title>
                          {municipality.name}: {amount} ações nesta exportação
                        </title>
                      </path>
                    );
                  })}
                </svg>
                <p className="muted">
                  Malha municipal: IBGE, referência de 23/10/2026. Sem
                  geocodificação ou localização individual.
                </p>
                <TextField
                  select
                  label="Selecionar município"
                  value={selected}
                  onChange={(event) => setSelected(event.target.value)}
                >
                  <MenuItem value="">Selecione um município</MenuItem>
                  {geography.municipalities.map((row) => (
                    <MenuItem value={row.id} key={row.id}>
                      {row.name}
                    </MenuItem>
                  ))}
                </TextField>
                <div
                  id="municipality-details"
                  className="published-map-details"
                  tabIndex={-1}
                  aria-live="polite"
                >
                  {selected ? (
                    <>
                      <h3>
                        {
                          geography.municipalities.find(
                            (row) => row.id === selected,
                          )?.name
                        }
                      </h3>
                      {city ? (
                        <>
                          <p>
                            {number(city.action_count)} ações incluem este
                            município.
                          </p>
                          <p>
                            Somente ações de município único:{" "}
                            {number(city.single_municipality_people)} pessoas e{" "}
                            {number(city.single_municipality_participations)}{" "}
                            participações.
                          </p>
                          <p>
                            {number(city.unallocated_action_count)} ações
                            incluem vários municípios e não possuem distribuição
                            de pessoas por cidade.
                          </p>
                        </>
                      ) : (
                        <p>
                          Sem ações neste município na exportação consultada.
                          Isso não comprova ausência histórica de atuação.
                        </p>
                      )}
                    </>
                  ) : (
                    <p>Selecione um município para ler seus dados.</p>
                  )}
                </div>
              </section>
              <section className="panel" aria-labelledby="table-title">
                <h2 id="table-title">Municípios nesta exportação</h2>
                <TextField
                  label="Buscar município"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
                <div
                  className="published-map-table"
                  role="region"
                  aria-label="Tabela de municípios"
                  tabIndex={0}
                >
                  <table>
                    <caption>
                      Presenças municipais; pessoas e participações apenas de
                      ações de município único
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Município</th>
                        <th scope="col">Ações</th>
                        <th scope="col">Pessoas</th>
                        <th scope="col">Participações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((row) => (
                        <tr key={row.code}>
                          <th scope="row">
                            <Button onClick={() => selectCity(row.code)}>
                              {row.name}
                            </Button>
                          </th>
                          <td>{number(row.action_count)}</td>
                          <td>{number(row.single_municipality_people)}</td>
                          <td>
                            {number(row.single_municipality_participations)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!filtered.length && (
                  <p role="status">Nenhum município corresponde à busca.</p>
                )}
                {filtered.length > 5 && (
                  <Pagination
                    aria-label="Páginas de municípios"
                    count={Math.ceil(filtered.length / 5)}
                    page={currentPage}
                    onChange={(_, value) => setPage(value)}
                  />
                )}
              </section>
            </>
          )}
          <section className="panel" aria-labelledby="distribution-title">
            <h2 id="distribution-title">Como interpretar os totais</h2>
            <p>
              Pessoas contempladas não representam pessoas únicas entre ações.
              Participações são contadas separadamente e não são somadas a
              atendimentos clínicos.
            </p>
            <p>
              Sem distribuição municipal:{" "}
              {number(data.summary.unallocated.action_count)} ações,{" "}
              {number(data.summary.unallocated.people_count)} pessoas e{" "}
              {number(data.summary.unallocated.participation_count)}{" "}
              participações.
            </p>
            <p>
              {number(data.summary.undated_action_count)} ações com data não
              informada. A data de captura não é a data das ações. A busca
              filtra somente os municípios apresentados; os totais acima
              permanecem globais.
            </p>
          </section>
        </>
      )}
    </>
  );
}
