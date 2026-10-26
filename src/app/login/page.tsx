"use client";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Alert,
  Button,
  IconButton,
  InputAdornment,
  TextField,
} from "@mui/material";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { FiEye, FiEyeOff, FiLock, FiMail, FiShield } from "react-icons/fi";
import { api, errorMessage } from "@/lib/api";
const schema = z.object({
  identifier: z.email("Informe um e-mail válido."),
  password: z.string().min(1, "Informe sua senha.").max(1024),
});
export default function LoginPage() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });
  async function submit(data: z.infer<typeof schema>) {
    setError("");
    try {
      await api.post("/auth/login", data);
      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      setError(errorMessage(error));
    }
  }
  return (
    <main id="conteudo" className="login-scene">
      <div className="login-stack">
        <div className="eyebrow">Acesso institucional | AC Actions Map</div>
        <section className="login-card" aria-labelledby="login-title">
          <Image
            className="brand-image"
            src="/logo-ac-social.png"
            alt="AC Social"
            width={80}
            height={80}
            priority
          />
          <h1 id="login-title">Entrar na plataforma</h1>
          <p>Use seu e-mail institucional e sua senha para continuar.</p>
          <form onSubmit={handleSubmit(submit)} noValidate>
            <div className="login-fields">
              <TextField
                label="E-mail"
                type="email"
                autoComplete="username"
                {...register("identifier")}
                error={!!errors.identifier}
                helperText={errors.identifier?.message}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <FiMail />
                      </InputAdornment>
                    ),
                  },
                }}
              />
              <TextField
                label="Senha"
                type={visible ? "text" : "password"}
                autoComplete="current-password"
                {...register("password")}
                error={!!errors.password}
                helperText={errors.password?.message}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <FiLock />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          type="button"
                          aria-label={
                            visible ? "Ocultar senha" : "Mostrar senha"
                          }
                          onClick={() => setVisible(!visible)}
                        >
                          {visible ? <FiEyeOff /> : <FiEye />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  },
                }}
              />
            </div>
            {error && (
              <Alert severity="error" sx={{ mb: 2, textAlign: "left" }}>
                {error}
              </Alert>
            )}
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isSubmitting}
            >
              {isSubmitting ? "Verificando acesso…" : "Acessar plataforma"}
            </Button>
          </form>
          <div className="support-box">
            <strong>
              <FiShield style={{ display: "inline", marginRight: 6 }} />
              Suporte de acesso
            </strong>
            <p>
              Precisa de suporte? Fale com a equipe administrativa da AC Social
              para liberar ou atualizar seu acesso.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
