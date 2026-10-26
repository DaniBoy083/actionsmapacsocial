"use client";
import { useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  TextField,
  useMediaQuery,
} from "@mui/material";
import { FiPlus, FiTrash2 } from "react-icons/fi";
import toast from "react-hot-toast";
import { api, errorMessage, type Action, type Municipality } from "@/lib/api";
import { useSession } from "@/components/session-context";

const schema = z
  .object({
    nome: z.string().trim().min(2, "Informe o nome da ação.").max(160),
    categoria: z.string().max(80),
    descricao: z.string().max(4000),
    resumo_publico: z.string().max(1000),
    inicio_em: z.string(),
    fim_em: z.string(),
    locais: z
      .array(
        z.object({
          municipio_ibge: z
            .string()
            .regex(/^25\d{5}$/, "Selecione um município."),
          nome_local: z.string().trim().max(160),
        }),
      )
      .min(1, "Adicione pelo menos um local.")
      .max(100),
  })
  .superRefine((data, ctx) => {
    if (data.fim_em && (!data.inicio_em || data.fim_em < data.inicio_em))
      ctx.addIssue({
        code: "custom",
        path: ["fim_em"],
        message: "Confira o período informado.",
      });
    const unique = new Set(
      data.locais.map(
        (p) => `${p.municipio_ibge}:${p.nome_local.toLocaleLowerCase()}`,
      ),
    );
    if (unique.size !== data.locais.length)
      ctx.addIssue({
        code: "custom",
        path: ["locais"],
        message: "Remova locais repetidos.",
      });
  });
type Fields = z.infer<typeof schema>;

export function ActionDialog({
  action,
  onClose,
}: {
  action?: Action;
  onClose: () => void;
}) {
  const session = useSession();
  const client = useQueryClient();
  const [failure, setFailure] = useState("");
  const mobile = useMediaQuery("(max-width:639px)");
  const municipalities = useQuery({
    queryKey: ["municipios"],
    queryFn: async () =>
      (await api.get<Municipality[]>("/localidades/pb")).data,
    staleTime: Infinity,
  });
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: action
      ? {
          ...action,
          inicio_em: action.inicio_em || "",
          fim_em: action.fim_em || "",
          locais: action.locais.map((p) => ({
            municipio_ibge: p.municipio_ibge,
            nome_local: p.nome_local,
          })),
        }
      : {
          nome: "",
          categoria: "",
          descricao: "",
          resumo_publico: "",
          inicio_em: "",
          fim_em: "",
          locais: [{ municipio_ibge: "", nome_local: "" }],
        },
  });
  const { fields, append, remove } = useFieldArray({ control, name: "locais" });
  function close() {
    if (
      !isSubmitting &&
      (!isDirty || window.confirm("Descartar as alterações não salvas?"))
    )
      onClose();
  }
  async function submit(values: Fields) {
    setFailure("");
    const payload = {
      ...values,
      inicio_em: values.inicio_em || null,
      fim_em: values.fim_em || null,
      versao: action?.versao || 0,
    };
    try {
      const options = { headers: { "X-CSRF-Token": session.csrf_token } };
      if (action) await api.patch(`/acoes/${action.id}`, payload, options);
      else await api.post("/acoes", payload, options);
      await client.invalidateQueries({ queryKey: ["acoes"] });
      await client.invalidateQueries({ queryKey: ["indicadores"] });
      toast.success(action ? "Ação atualizada." : "Ação cadastrada.");
      onClose();
    } catch (error) {
      setFailure(errorMessage(error));
    }
  }
  return (
    <Dialog
      open
      onClose={close}
      fullWidth
      maxWidth="md"
      fullScreen={mobile}
      aria-labelledby="action-title"
    >
      <form onSubmit={handleSubmit(submit)} noValidate>
        <DialogTitle id="action-title">
          {action ? "Editar ação" : "Cadastrar nova ação"}
        </DialogTitle>
        <DialogContent>
          <p className="muted">
            Registre as informações gerais e todos os locais de realização. O
            cadastro será salvo como rascunho.
          </p>
          {failure && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {failure}
            </Alert>
          )}
          <div className="form-grid">
            <TextField
              autoFocus
              label="Nome da ação"
              required
              {...register("nome")}
              error={!!errors.nome}
              helperText={errors.nome?.message}
            />
            <div className="form-two">
              <TextField
                label="Data inicial"
                type="date"
                {...register("inicio_em")}
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                label="Data final"
                type="date"
                {...register("fim_em")}
                error={!!errors.fim_em}
                helperText={errors.fim_em?.message}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </div>
            <TextField
              label="Categoria (opcional)"
              {...register("categoria")}
            />
            <TextField
              label="Descrição interna (opcional)"
              multiline
              minRows={2}
              {...register("descricao")}
            />
            <TextField
              label="Resumo público para revisão (opcional)"
              multiline
              minRows={2}
              {...register("resumo_publico")}
              helperText="Sem nomes de beneficiários, documentos ou informações privadas. Não publica automaticamente."
            />
            <h2 style={{ fontSize: 18, margin: 0 }}>Locais de realização</h2>
            {municipalities.isError && (
              <Alert severity="error">
                Não foi possível carregar os municípios.{" "}
                <Button onClick={() => municipalities.refetch()}>
                  Tentar novamente
                </Button>
              </Alert>
            )}
            {fields.map((field, index) => (
              <div className="location-row" key={field.id}>
                <Controller
                  control={control}
                  name={`locais.${index}.municipio_ibge`}
                  render={({ field: selectField }) => (
                    <TextField
                      select
                      label={`Município do local ${index + 1}`}
                      required
                      {...selectField}
                      error={!!errors.locais?.[index]?.municipio_ibge}
                      helperText={
                        errors.locais?.[index]?.municipio_ibge?.message
                      }
                      disabled={municipalities.isPending}
                    >
                      <MenuItem value="">Selecione</MenuItem>
                      {municipalities.data?.map((p) => (
                        <MenuItem value={p.codigo} key={p.codigo}>
                          {p.nome}
                        </MenuItem>
                      ))}
                    </TextField>
                  )}
                />
                <TextField
                  label={`Nome do local ${index + 1} (opcional)`}
                  {...register(`locais.${index}.nome_local`)}
                />
                <Button
                  aria-label={`Remover local ${index + 1}`}
                  disabled={fields.length === 1}
                  onClick={() => remove(index)}
                >
                  <FiTrash2 />
                </Button>
              </div>
            ))}
            {errors.locais?.root?.message && (
              <Alert severity="error">{errors.locais.root.message}</Alert>
            )}
            {errors.locais?.message && (
              <Alert severity="error">{errors.locais.message}</Alert>
            )}
            <Button
              variant="outlined"
              startIcon={<FiPlus />}
              onClick={() => append({ municipio_ibge: "", nome_local: "" })}
              disabled={fields.length >= 100}
            >
              Adicionar local
            </Button>
          </div>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={close} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={isSubmitting || !municipalities.data}
          >
            {isSubmitting ? "Salvando…" : "Salvar rascunho"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
