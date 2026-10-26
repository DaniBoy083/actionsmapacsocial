# Branding e design system base

Estado de conformidade e pendencias atuais: [auditoria da aplicacao](AUDITORIA_APLICACAO_E_PRINCIPIOS.md). Este guia nao substitui os criterios de aceite registrados nessa auditoria.

Este documento descreve o esquema visual, os padrões de composição e as regras de uso que definem a identidade visual da aplicação AC Social / Agenda Digital. Ele foi criado para que outras aplicações que usem este projeto como base mantenham a mesma linguagem visual, consistência e clareza.

Revisão de 2026-09-14: conferência estática de layout, sidebar e footer. Medidas recomendadas de acessibilidade, contraste e responsividade ainda precisam de validação visual; não representam auditoria concluída em navegador.

## 1. Objetivo da identidade

A marca prioriza:
- cuidado social e acolhimento
- clareza visual e hierarquia forte
- profissionalismo administrativo
- uso de interfaces limpas, com foco em decisões rápidas e leitura fácil

A estética combina uma base neutra com acentos quentes e reforços de urgência em ações primárias.

---

## 2. Paleta de cores

### Cores primárias

- Vermelho principal: `#ef1636`
  - uso principal em botões de ação, destaques, seleções e foco
- Vermelho escuro: `#b80d27`
  - texto e estados de alerta/ação secundária
- Marrom escuro / vinho: `#65111f`
  - textos principais, títulos e ícones de alto contraste
- Rosa muito claro: `#fff8f9`
  - fundos de filtros, cards e blocos de alerta
- Branco: `#ffffff`
  - base de telas e superfícies de leitura

### Cores complementares

- Amarelo suave: `#fff8d9`
  - alertas e avisos
- Dourado: `#f1cc6f` / `#d8ae37`
  - destaques de atenção e elementos de sinalização
- Cinza de texto: `#6f2a36`
  - textos de apoio e labels secundários
- Cinza de borda: `#ef163624`
  - bordas sutis e separadores

### Regras de uso

- O vermelho deve ser a cor de ação principal, mas não deve dominar toda a tela.
- Fundo geral deve permanecer claro e limpo, com contraste elevado para texto.
- Campos de filtro e seleção devem usar fundos em `#fff8f9` com borda em `#ef163624`.
- Alertas e estados importantes podem usar o amarelo suave com texto em marrom escuro.

---

## 3. Tipografia

### Hierarquia recomendada

- Títulos de página: peso forte, visual de destaque, cor em vinho ou preto
- Labels e controles: peso médio/semibold, cor de texto principal
- Texto de apoio: menor, mais suave, em cinza escuro ou vináceo

### Recomendações de uso

- Evitar excesso de estilos diferentes na mesma tela.
- Manter bom contraste entre texto e fundo.
- Usar negrito para destacar filtros, botões e valores de dados críticos.

---

## 4. Espaçamento e grid

O sistema usa uma lógica de espaçamento visual simples e consistente.

### Padrões

- Espaçamento base: 4px
- Escala recomendada: 4, 8, 12, 16, 20, 24, 32
- Bordas arredondadas: 0.8rem a 1rem em cards e controles
- Altura mínima de controles: 44 a 52px para melhor acessibilidade

### Diretrizes de composição

- Agrupar filtros em linha ou grade, respeitando fluidez responsiva.
- Deixar espaço suficiente entre blocos para leitura, sem telas congestionadas.
- Usar padding uniforme em cards, inputs e botões para manter consistência.
- A sidebar usa posicionamento fixo; a área principal reserva espaço lateral quando ela está comprimida e, a partir de `sm`, também quando expandida. No mobile expandido há sobreposição: sidebar `w-full` e conteúdo `pl-0`.
- No mobile, a sidebar expandida ocupa `w-full`; em telas maiores, usa `19.375rem` (`w-77.5`)
- A sidebar comprimida usa `5rem` (`w-20`) no mobile e `5.75rem` (`w-23`) em telas maiores
- A área principal deve usar `min-w-0` e o padding lateral correspondente ao estado da sidebar para permitir que grids e textos se adaptem sem serem encobertos

---

## 5. Estilo de componentes

### Botões

- Botão primário: fundo vermelho, texto branco, hover mais escuro
- Botão secundário: fundo branco ou rosa claro, borda vermelha suave, texto vinho
- Botão de alerta: fundo amarelo suave, borda dourada e texto marrom escuro
- Botão desabilitado: opacidade reduzida e cursor bloqueado

### Inputs e filtros

- Fundo: `#fff8f9`
- Borda: `#ef163624`
- Texto principal: `#65111f`
- Ícones: vermelho principal
- Campos de busca devem manter o mesmo padrão visual dos filtros de agenda

### Cards e painéis

- Fundo branco
- Borda discreta em vermelho suave
- Espaçamento interno consistente
- Títulos com destaque forte e textos de suporte com contraste adequado

### Modais

- Layout centralizado
- Fundo claro e bordas discretas
- Botões de ação de forma bem definida e hierarquizada
- Ações destrutivas ou críticas devem manter destaque visual sem exagerar no contraste

### Footer institucional

- É renderizado no layout raiz nas páginas que o utilizam; `global-error.tsx` possui documento próprio e atualmente não inclui o footer. Não se aplica a respostas de API.
- Deve existir uma única instância por página, evitando duplicação em layouts específicos
- Fundo atual em `#8f0d23`, conforme `InstitutionalFooter.tsx`, com texto branco e borda superior branca translúcida. `#65111f` permanece como cor de textos na paleta; eventual mudança do footer exige decisão visual.
- Conteúdo centralizado em largura máxima, com empilhamento no mobile e alinhamento à esquerda em telas maiores
- Identificação principal: `AC Social | Agenda Digital`
- Texto de apoio: `Ambiente institucional para recepção, atendimento e administração.`

---

## 6. Padrões de layout

### Estrutura recomendada

- Sidebar lateral com fundo vermelho e itens em destaque visual
- Área principal clara, com blocos e cards em fundo branco
- Filtros e ações no topo da área principal
- Tabela ou painel de dados em base branca com linhas claras e separadores suaves
- Footer institucional global na base da aplicação, com fundo vinho e identificação do ecossistema AC Social

### Regras visuais

- Posicionar ações principais logo acima do conteúdo relevante
- A área de filtros deve ter suporte visual forte, mas sem competir com a tabela ou painel principal
- Usar contraste regular e espaços consistentes para manter a interface organizada

---

## 7. Comportamento visual

### Estados

- Hover: escurecer o vermelho ou aumentar contraste na borda
- Focus: manter linha/indicador claro e legível
- Selected: vermelho principal com alto contraste
- Disabled: reduzir intensidade visual sem apagar completamente o elemento

### Responsividade

- Componentes devem se adaptar bem em telas menores sem perder legibilidade
- Filtros devem empilhar ou reorganizar de forma natural
- Grids devem preservar hierarquia de conteúdo e ações principais
- A sidebar usa posicionamento fixo e mantém sua altura limitada pela área do footer institucional por meio de `--panel-footer-overlap`
- O conteúdo interno da sidebar é dividido entre cabeçalho, área central rolável e rodapé fixo; informações da equipe e ferramentas ficam no rodapé
- Em telas a partir de `sm`, a transição altera largura e padding reservado. No mobile, a sidebar expandida cobre a área principal; validar acesso aos controles de recolhimento e retorno ao conteúdo em uma futura conferência visual.

---

## 8. Regras de consistência

Para preservar a imagem da marca, todas as aplicações baseadas neste projeto devem:

- manter a paleta principal aproximada aos valores acima
- priorizar fundo claro com acentos em vermelho e vinho
- usar bordas suaves e espaçamentos consistentes
- manter a lógica de hierarquia visual da interface: ação principal > filtro > conteúdo > suporte
- evitar criar variações coloridas sem necessidade para manter coesão visual

---

## 9. Exemplo de tokens de CSS

```css
:root {
  --brand-red: #ef1636;
  --brand-red-dark: #b80d27;
  --brand-wine: #65111f;
  --brand-rose: #fff8f9;
  --brand-warning-bg: #fff8d9;
  --brand-warning-border: #f1cc6f;
  --brand-white: #ffffff;
  --brand-border-soft: #ef163624;
  --brand-text-muted: #6f2a36;
}
```

---

## 10. Resumo executivo

A identidade visual deste projeto é definida por:
- vermelho como ação e prioridade
- fundo claro e limpo
- texto em vinho e marrom escuro
- bordas suaves e filtros bem delineados
- layout funcional, administrativo e de fácil leitura

Seguindo esse esquema, qualquer aplicação que use esta base como referência manterá coerência visual com o ecossistema AC Social.
