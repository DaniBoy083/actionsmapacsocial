# Implementação necessária na Agenda Digital

## Estado e responsabilidade

O receptor foi implementado na **Agenda Digital**, junto à exportação de ações para a Plataforma. As APIs existentes `/api/analytics` e `/api/analytics/atendimentos` permanecem separadas dos dados de ações. Código na Agenda: `src/modules/actions-map`, migração `202610260001` e documentação `docs/actions-map-summary.md`.

Fluxo obrigatório: **AC Actions Map → Agenda Digital → Plataforma Consolidada de Dados → Portal Institucional**. O módulo não chama diretamente a Plataforma ou o Portal para publicar. Não transportar beneficiários ou identidades de profissionais no pipeline.

## 1. Receptor versionado

`POST /api/integracoes/v1/acoes/resumos` recebe o contrato **1.1**. O SHA-256 da credencial exclusiva fica em `ACTIONS_MAP_TOKEN_SHA256`. Um GET na mesma rota, com `acao_id` e a mesma credencial, confere o snapshot persistido. `GET /api/analytics/acoes` exporta ações publicadas usando a chave institucional de analytics.

Headers obrigatórios: `Authorization: Bearer <credencial de serviço>`, `Idempotency-Key`, `Content-Type: application/json`. Somente HTTPS; token exclusivo por aplicação/ambiente, escopo `acoes.resumos.write`, rotação/revogação com auditoria e autorização reforçada. Guardar hash do token no receptor; nunca registrar headers ou o corpo completo.

Payload de exemplo sintético:

```json
{
  "schema_version": "1.1",
  "event_id": "d2e316e8-e289-4289-ae29-32d4cb73eaaf",
  "source": "ac-actions-map",
  "acao_id": "7b94c4ed-ddbc-40b1-a695-2b48137f979c",
  "revisao": 2,
  "operacao": "upsert",
  "categoria": "mobilizacao",
  "inicio_em": "2026-10-01",
  "fim_em": null,
  "municipios_ibge": ["2507507", "2504009"],
  "quantidade_acoes": 1,
  "quantidade_participacoes": 12,
  "quantidade_pessoas_contempladas": 12,
  "publicavel": false
}
```

O schema executável está em `backend/app/domain/contracts.py` (`Summary`). `acao_id` é um ID técnico de ação. `quantidade_pessoas_contempladas` conta IDs distintos do cadastro próprio dentro da ação; nomes não definem identidade. `publicavel` só é verdadeiro para ação publicada após aprovação. Títulos, textos editoriais e dados individuais não são enviados. A Melhor Visão informa **50 pessoas contempladas, 1 ação e município IBGE 2508901 (Mamanguape)**.

Rejeitar campos extras em **todas as profundidades**, tipos inválidos, municípios fora do catálogo PB, quantidades negativas, fonte/versão desconhecida e corpo excessivo. Não aceitar listas de pessoas, nomes, CPF, nascimento, telefone, e-mail, endereços privados, prontuários ou `usuario_id`.

## 2. Recebimento transacional e idempotência

1. Autenticar/autorizar a credencial e aplicar limite de requisições por cliente.
2. Validar esquema e calcular hash canônico do conteúdo.
3. Gravar na mesma transação inbox e snapshot corrente por ação/revisão. A Plataforma consulta os snapshots publicados em `/api/analytics/acoes`, com 100 itens por página e totais sobre o conjunto corrente.
4. Constraint única por `(cliente, idempotency_key)` e por `(source, event_id)`. Mesmo evento/chave com conteúdo diferente retorna **409**. Concorrência deve usar constraint SQL, não só verificação prévia.
5. Retry com conteúdo idêntico devolve o mesmo reconhecimento sem gerar outro efeito.
6. Somente após commit, responder 200/202 com o ACK abaixo. Um 2xx vazio não confirma entrega para o worker atual.

```json
{
  "schema_version": "1.1",
  "event_id": "d2e316e8-e289-4289-ae29-32d4cb73eaaf",
  "status": "accepted"
}
```

Para repetição legítima, `status: "duplicate"`. Falhas de autenticação: 401; escopo: 403; esquema: 422; conflito: 409; limite: 429; indisponibilidade temporária: 503. Erros sanitizados, sem refletir conteúdo sensível. A fila do Map retenta com backoff, até dez tentativas; não bloqueia o cadastro da ação. Adicionar replay manual auditável e reconciliação antes de produção.

## 3. Semântica e ordenação

Os eventos são **snapshots de substituição**, não incrementos. Upsert pela chave `(source, acao_id)` somente se `revisao` for maior que a vigente. Uma revisão antiga entregue depois de uma nova é reconhecida/armazenada sem substituir o snapshot recente. Não somar eventos nem revisões para calcular indicadores.

- Uma ação em três municípios é **uma ação global**, com presença em três recortes municipais.
- `quantidade_participacoes` é total global da ação. **Não dividir nem replicar como total de beneficiários por município.** Ainda não existe recorte municipal seguro de participações neste contrato.
- `operacao: "archive"` substitui o snapshot anterior e informa zero nas quantidades ativas. Preservar auditoria e evitar reaparecimento por evento antigo.
- Pessoas contempladas são contadas dentro de cada ação. Não interpretar sua soma entre ações como pessoas únicas globais nem somar com atendimentos clínicos.
- O campo `publicavel` é uma elegibilidade técnica futura, não aprovação automática da Plataforma. Suprimir células pequenas e combinações de risco conforme governança aprovada; não fixar um limiar sem validação institucional.

## 4. Encaminhamento para a Plataforma

A exportação privada `/api/analytics/acoes?page=1` foi implementada, preservando a API clínica anterior. A Plataforma ainda precisa cadastrar essa fonte, percorrer páginas e substituir snapshots por origem/ação/revisão. A recepção na Agenda não prova atualização do mapa público.

Na Plataforma: versionar a ingestão, reconciliar fonte/eventos, aprovar conteúdo público e implementar projeção por allowlist. Somente a API pública da Plataforma alimentará o Portal. Planejar retirada do CRUD antigo do Portal com um único escritor e rollback da origem de leitura.

## 5. Identidade e operação na Agenda

- Preservar `profissionais_cadastrados`, `user_type=administracao` e vínculo real de equipes. O Map já consulta esses dados sem criar senha paralela.
- Documentar uma estratégia explícita de conta ativa/revogação; o schema atual verificado não possui flag de atividade.
- Se for escolhido SSO entre aplicações, definir emissão/validação de sessão e audiência; não compartilhar cookies ou segredos por cópia informal. O Map usa sessão própria, com as mesmas credenciais institucionais.
- Provisionar URL pública da Agenda para o atalho `AGENDA_WEB_URL`. Sem URL confirmada o atalho não aponta para destino inventado.
- Diagnóstico de Tecnologia: eventos recebidos, pendentes/entregues, última confirmação, quantidade de tentativas e códigos seguros de erro. Administração não consulta tokens ou diagnósticos técnicos.

## 6. Aceite antes de ativar

- [ ] Endpoint, esquema, fonte e credenciais homologados em staging.
- [ ] Reenvio idêntico produz um efeito; conteúdo divergente gera 409.
- [ ] Entrega fora de ordem não restaura snapshot antigo; arquivamento remove totais ativos.
- [ ] Município múltiplo não duplica o total global e não distribui participações indevidamente.
- [ ] Banco/Agenda/Plataforma indisponíveis preservam operações e retomam com backoff.
- [ ] Nenhum campo nominal, identificador individual ou dado clínico atravessa o fluxo.
- [ ] Logs, rotação/revogação, monitoramento e replay auditável testados.
- [ ] Backups/restauração e rollback testados; responsáveis aprovam a virada do escritor do Portal.

As variáveis privadas `AGENDA_SUMMARIES_URL` e `AGENDA_SERVICE_TOKEN` configuram o backend. O PostgreSQL usa `FOR UPDATE SKIP LOCKED`. Mutações bem-sucedidas disparam tentativa em background, respeitando backoff. Versões superadas são marcadas `substituido`; contratos anteriores aguardam republicação. Somente ACK 1.1 do evento confirma entrega. Tecnologia dispõe de sincronização manual autenticada e auditada. O worker também roda por CLI; seu agendamento para retentativas sem tráfego permanece responsabilidade operacional.
