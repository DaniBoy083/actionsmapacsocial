"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, TextField } from "@mui/material";
import { api, errorMessage } from "@/lib/api";

export default function OperationalLogin() {
  const router = useRouter();
  const queries = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  const context = useQuery({
    queryKey: ["auth-context"],
    retry: false,
    staleTime: 0,
    queryFn: async () =>
      (
        await api.get<{ demonstracao: boolean; acesso_operacional: boolean }>(
          "/auth/context",
        )
      ).data,
  });
  async function login(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      await api.post("/operacao/auth/login", {
        identifier: username,
        password,
      });
      queries.clear();
      router.replace("/operacao");
      router.refresh();
    } catch (error) {
      setFailure(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="conteudo" className="login-scene">
      <div className="login-stack">
        <section
          className="login-card"
          aria-labelledby="operational-login-title"
        >
          <Image
            className="brand-image"
            src="/logo-ac-social.png"
            unoptimized
            alt="AC Social"
            width={80}
            height={80}
            priority
          />
          <h1 id="operational-login-title">Acesso da equipe da ação</h1>
          <p>
            Oftalmologista, optometrista e recepção entram com seu usuário
            individual do Actions Map.
          </p>
          {context.data?.demonstracao && (
            <Alert severity="warning" sx={{ mb: 2, textAlign: "left" }}>
              <strong>Demonstração · dados fictícios</strong>
              <p>Escolha um perfil para preencher o acesso de exemplo.</p>
              <div className="demo-accesses">
                {[
                  ["Oftalmologista", "oftalmo.demo"],
                  ["Optometrista", "opto.demo"],
                  ["Recepção", "recepcao.demo"],
                ].map(([label, user]) => (
                  <Button
                    key={user}
                    type="button"
                    variant="outlined"
                    onClick={() => {
                      setUsername(user);
                      setPassword("Demonstracao-local-2026!");
                      setFailure("");
                    }}
                  >
                    Preencher acesso de {label}
                  </Button>
                ))}
              </div>
            </Alert>
          )}
          {context.data && !context.data.acesso_operacional && (
            <Alert severity="info" sx={{ mb: 2 }}>
              O acesso operacional aguarda liberação da equipe responsável.
            </Alert>
          )}
          <form onSubmit={login}>
            <div className="login-fields">
              <TextField
                label="Usuário do Actions Map"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                slotProps={{ htmlInput: { maxLength: 80 } }}
              />
              <TextField
                label="Senha"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                slotProps={{ htmlInput: { maxLength: 128 } }}
              />
            </div>
            {failure && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {failure}
              </Alert>
            )}
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={busy || !context.data?.acesso_operacional}
            >
              {busy ? "Verificando acesso…" : "Entrar na minha ação"}
            </Button>
          </form>
          <p>
            Seu acesso e as ações disponíveis são definidos pela Administração.
            Solicite suporte para criação ou redefinição da senha.
          </p>
          {context.data?.demonstracao && (
            <Link href="/login">
              Demonstração de Administração e Tecnologia
            </Link>
          )}
        </section>
      </div>
    </main>
  );
}
