# Plano de implementação — Mapa de Ações no Portal Institucional

**Projeto:** Portal Institucional AC Social  
**Escopo:** somente o Portal Institucional  
**Objetivo:** consumir os dados de ações disponibilizados pela **API da Plataforma Consolidada de Análise de Dados** e atualizar automaticamente a visualização do Mapa de Ações no Portal, preservando sua arquitetura, identidade visual e requisitos de segurança.

## 1. Contexto da integração

O fluxo de dados já definido no ecossistema é:

```text
Actions Map
    ↓
Agenda Digital
    ↓
Plataforma Consolidada de Análise de Dados
    ↓ API de leitura
Portal Institucional
    ↓
Mapa de Ações atualizado
```

O Portal **não** deve consultar diretamente o Actions Map ou a Agenda Digital. Sua única fonte de dados para esse recurso é a API da Plataforma Consolidada. Não está neste escopo desenvolver ou alterar os outros sistemas.

## 2. Resultado esperado

- Substituir fontes estáticas, mocks ou dados antigos do mapa pela resposta da API da Plataforma Consolidada.
- Representar as ações recebidas no mapa atual do Portal, de acordo com os campos e coordenadas disponíveis.
- Manter os dados atualizados conforme a estratégia de revalidação definida; não depender de edição manual do Portal.
- Exibir informações públicas essenciais de cada ação ao selecionar um marcador/região.
- Tratar indisponibilidade, dados incompletos, ausência de ações e erros de integração sem quebrar o Portal.
- Manter o estilo do Portal e a experiência responsiva e acessível.

## 3. Confirmações iniciais — contrato da API

Antes de conectar a interface, validar na documentação ou na resposta real da API existente:

1. **Endpoint e método** de consulta (por exemplo, `GET <endpoint-existente>`; **não** presumir uma rota específica).
2. **Autenticação**, se necessária, e política de acesso a dados públicos.
3. **Formato do payload**, paginação, filtros, ordenação e metadados de atualização.
4. **Campos geográficos** disponíveis: latitude/longitude, endereço, município/UF ou outra referência.
5. **Identificador estável** por ação e campo de alteração (`updatedAt` ou equivalente).
6. **Tratamento de status**: ativa, concluída, agendada, cancelada etc., se esses valores existirem.
7. **Limites de requisições e política de cache**.

> Os nomes exatos de rotas, atributos e estados devem ser extraídos do contrato real da Plataforma Consolidada; os exemplos abaixo são um modelo **interno do Portal**, não uma afirmação sobre o payload existente.

## 4. Arquitetura proposta — apenas Portal

```text
Portal Institucional (Next.js + TypeScript)
    │
    ├── Camada de integração / serviço de leitura
    │      ├── URL da Plataforma Consolidada via variável de ambiente
    │      ├── Requisição e tratamento de erros
    │      ├── Validação do payload
    │      └── Normalização para modelo interno
    │
    ├── Camada de dados / estado
    │      ├── Cache e revalidação
    │      ├── Estados loading, empty, error
    │      └── Filtros opcionais
    │
    └── Mapa de Ações (componente existente)
           ├── Marcadores / camadas
           ├── Detalhes da ação
           ├── Legenda e filtros (se aplicáveis)
           └── Acessibilidade e responsividade
```

**Preferência:** reutilizar o componente, a biblioteca de mapas e o design atualmente utilizados no Portal. Evitar uma reescrita desnecessária.

**Segurança da consulta:** se a API exigir token privado, fazer a chamada **no servidor do Next.js** (Server Component, função server-only ou rota interna), mantendo credenciais fora do JavaScript enviado ao navegador. Se a API for pública e permitir acesso direto do browser com CORS apropriado, avaliar a alternativa de chamada cliente, sem incluir segredos.

## 5. Modelo interno e normalização

Definir um tipo de apresentação estável no Portal, ajustado após inspecionar o payload real:

```ts
type MapAction = {
  id: string;
  title: string;
  description?: string;
  category?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
  locationLabel?: string;
  city?: string;
  state?: string;
  latitude?: number;
  longitude?: number;
  updatedAt?: string;
};
```

Criar uma função de transformação para converter **a resposta real** da API nesse formato. Garantir:

- `id` único e estável para marcadores/listagens;
- validação de latitude (-90 a 90) e longitude (-180 a 180);
- datas e textos formatados em pt-BR;
- ausência de campos opcionais sem travar a renderização;
- deduplicação somente quando houver evidência de duplicidade pela chave definida;
- tratamento explícito de ações sem localização válida.

**Atenção:** quando houver apenas endereço ou município, não inventar coordenadas. Usar um serviço de geocodificação **somente se** isso fizer parte da solução aprovada, com cache, limites e cuidados de privacidade; do contrário, mostrar a ação em lista complementar com localização textual.

## 6. Etapas de execução

### Etapa 1 — Inspeção do Portal e da API

- Localizar página/seção, componentes e fonte de dados atuais do Mapa de Ações.
- Conferir endpoint existente da Plataforma, payload real, esquema de autenticação e filtros.
- Identificar quais campos são seguros para exposição no Portal público.
- Registrar um exemplo de payload com dados fictícios para testes e mapear atributos reais → `MapAction`.

**Saída:** contrato de consumo validado e pontos de integração identificados.

### Etapa 2 — Criar a camada de consumo no Portal

- Configurar variável de ambiente para a URL base da API (ex.: `PLATFORM_API_BASE_URL`, nome a adequar ao padrão do repositório).
- Configurar segredo exclusivamente no servidor, caso necessário, sem prefixo `NEXT_PUBLIC_`.
- Implementar um serviço de leitura desacoplado da interface.
- Validar e normalizar a resposta; tipagem TypeScript não substitui validação em runtime.
- Tratar respostas não-200, timeout, lista vazia e formato inesperado.

**Saída:** serviço tipado que entrega `MapAction[]` para a interface.

### Etapa 3 — Integrar ao Mapa de Ações existente

- Remover a dependência dos dados antigos/estáticos quando a integração estiver validada.
- Alimentar o mapa com as ações normalizadas.
- Reaproveitar marcadores, popups/cards, legenda e interações existentes.
- Ajustar enquadramento do mapa para os pontos válidos, com zoom inicial seguro se não houver pontos.
- Garantir que ações sem coordenadas válidas não gerem erro nem apareçam em lugar incorreto.
- Preservar identidade visual e funcionamento em dispositivos móveis.

**Saída:** mapa renderizado a partir da Plataforma Consolidada.

### Etapa 4 — Sincronização, cache e resiliência

- Definir a frequência de atualização de acordo com a necessidade institucional e os limites reais da API.
- Usar o mecanismo de cache/revalidação mais adequado ao caminho adotado: `fetch` do Next.js no servidor ou TanStack Query/React Query no cliente.
- Evitar múltiplas consultas simultâneas desnecessárias ao mesmo endpoint.
- Se houver cache válido, considerar exibir a última versão conhecida em falhas temporárias, com indicação discreta de atualização.
- Não prometer tempo real: **polling/revalidação periódica só produz atualização conforme o intervalo configurado**.

**Saída:** mapa atualizado automaticamente, com comportamento previsível em falhas.

### Etapa 5 — UX, privacidade e acessibilidade

- Estados de interface: carregamento, nenhuma ação cadastrada, erro de atualização e sucesso.
- Popups acessíveis por teclado, labels claros e alternativa textual/lista para conteúdo essencial.
- Contraste adequado, layout responsivo e interação utilizável em telas menores.
- Expor somente dados aprovados para uso público; não publicar identificadores pessoais, contatos privados, endereços sensíveis ou dados assistenciais.
- Sanitizar conteúdo textual recebido antes de exibi-lo.

**Saída:** experiência pública confiável e adequada ao Portal.

### Etapa 6 — Testes, observabilidade e publicação

- Testes da normalização: payload válido, campo ausente, localização inválida, lista vazia e duplicação.
- Testes de integração: sucesso da API, timeout, 401/403, 404/500 e JSON fora do contrato.
- Testes da interface: quantidade/posição de marcadores, detalhes da ação, responsividade e acessibilidade.
- Registrar erros de requisição e validação sem armazenar credenciais ou dados privados em logs.
- Homologar com ações reais em ambiente de teste e realizar publicação gradual.
- Verificar em produção se o mapa reflete uma alteração efetivamente propagada à API da Plataforma.

**Saída:** recurso homologado e monitorável.

## 7. Estrutura sugerida de código

Adaptar ao arranjo atual do repositório (App Router, pastas e convenções existentes):

```text
src/
  features/
    actions-map/
      types.ts              # Modelo interno MapAction
      schemas.ts            # Validação da resposta externa
      mapper.ts             # Payload da Plataforma → MapAction
      service.ts            # Consumo da API / estratégia de cache
      components/
        ActionsMap.tsx      # Reutilizar/adaptar componente existente
        ActionDetails.tsx
        ActionsMapState.tsx
```

Isso é uma **organização de referência**, não uma exigência para reorganizar pastas que já funcionem.

## 8. Critérios de aceite

- [ ] O Portal consulta **somente** a API da Plataforma Consolidada para obter as ações.
- [ ] As ações disponíveis no endpoint aprovado aparecem no mapa quando possuem coordenadas válidas.
- [ ] A visualização preserva o design e as interações do mapa existente.
- [ ] Alterações na API passam a ser refletidas no Portal dentro da política de atualização configurada.
- [ ] Dados incorretos ou sem localização não quebram o mapa e possuem tratamento definido.
- [ ] Erros temporários não derrubam a página institucional.
- [ ] Nenhuma credencial privada é exposta no bundle do navegador.
- [ ] Somente dados publicáveis são exibidos, conforme LGPD e política institucional.
- [ ] A solução funciona em desktop e mobile, com alternativa acessível para leitura das ações.
- [ ] Testes e validação em produção comprovam o fluxo de ponta a ponta já integrado.

## 9. Limites do escopo

**Incluído:** leitura, validação, normalização, apresentação, atualização e monitoramento do Mapa de Ações **dentro do Portal Institucional**.

**Não incluído:** qualquer desenvolvimento ou alteração no Actions Map, na Agenda Digital ou na Plataforma Consolidada; reestruturação geral do Portal; criação de fluxo de cadastro/edição de ações no Portal; alterações no banco de dados central.

## 10. Ordem prática recomendada

**Inspecionar contrato real → Implementar serviço e mapeamento → Conectar ao mapa existente → Adicionar revalidação/resiliência → Testar e publicar.**

**Ponto de atenção:** como a API já foi ampliada, o principal risco é presumir nomes de campos, formato geográfico ou autenticação antes de consultar seu contrato real. A integração do Portal deve se ajustar a esse contrato, sem replicar lógica de negócio dos sistemas upstream.
