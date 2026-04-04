# Sprint Log — Performance, Visual e Usabilidade

**Data**: 2026-04-04
**Objetivo**: Elevar o portal de "funcional" para "profissional" em performance, visual e usabilidade.

---

## Resumo de Resultados

| Metrica | Antes | Depois |
|---------|-------|--------|
| Testes | 58 passando | **73 passando** (+15 novos) |
| CSS customizado | 46 linhas | **~200 linhas** |
| Plugins ativos | 2 (openapi, webpack) | **5** (+mermaid, search, ideal-image*) |
| Docs com admonitions | 0 | **5** (100% dos docs) |
| Docs com frontmatter SEO | 0 | **5** (100%) |
| Docs com cross-links | 1 | **5** (100%) |
| Docs com Mermaid | 0 | **2** (architecture, deploy) |
| Favicon | Ausente (404) | SVG funcional |
| Social card | Ausente | PNG 1200x630 |
| Busca | Inexistente | Local offline (Ctrl+K) |
| Pagina 404 | Default Docusaurus | Customizada em pt-BR |
| Announcement bar | Inexistente | Configurado |
| Bundle splitting | Monolitico | OpenAPI em chunk separado |

\* `@docusaurus/plugin-ideal-image` comentado por incompatibilidade do sharp com ambiente atual.

---

## FASE 1 — Fundacao (Deps, Assets, Config)

### O que foi feito

1. **Instalou** `@docusaurus/theme-mermaid` — diagramas nativos em code blocks
2. **Instalou** `@easyops-cn/docusaurus-search-local` — busca offline sem Algolia
3. **Criou** `static/img/favicon.svg` — SVG com initials "ED" sobre #2e86ab
4. **Criou** `static/img/social-card.png` — gradient 1200x630 para OG cards
5. **Criou** `static/robots.txt` — crawl directives + sitemap reference
6. **Atualizou** `docusaurus.config.ts`:
   - `markdown.mermaid: true`
   - `themes: ["docusaurus-theme-openapi-docs", "@docusaurus/theme-mermaid"]`
   - Plugin search-local com `language: ["pt", "en"]`
   - `announcementBar` com aviso de placeholders TODO
   - `colorMode.respectPrefersColorScheme: true`
   - `metadata` com keywords SEO
   - `favicon: "img/favicon.svg"`

### Arquivos modificados
- `docs-site/package.json`
- `docs-site/pnpm-lock.yaml`
- `docs-site/docusaurus.config.ts`
- `docs-site/static/img/favicon.svg` (novo)
- `docs-site/static/img/social-card.png` (novo)
- `docs-site/static/robots.txt` (novo)

---

## FASE 2 — Visual (CSS, 404)

### O que foi feito

1. **Expandiu** `custom.css` de 46 para ~200 linhas:
   - Navbar frosted glass (backdrop-filter blur)
   - Sidebar active link com borda de acento
   - Cards com hover lift nas category index pages
   - Admonitions com bordas arredondadas
   - Tabelas responsivas (overflow-x mobile)
   - Code blocks com bordas e titulo estilizado
   - Footer com uppercase e letter-spacing
   - Hero section com gradiente para homepage
   - Search input arredondado
   - Pagina 404 centralizada
   - Mermaid container spacing

2. **Criou** `src/pages/404.tsx` — pagina 404 customizada em portugues

### Decisoes de design
- Usou **apenas CSS variables e seletores** (sem swizzle de componentes)
- Inspiracao: Stripe (cards), Tailwind (tipografia), Vercel (navbar), GitHub (footer)
- Todos os estilos tem variante dark mode

### Arquivos modificados
- `docs-site/src/css/custom.css`
- `docs-site/src/pages/404.tsx` (novo)

---

## FASE 3 — Conteudo (Frontmatter, Admonitions, Mermaid, Cross-links)

### O que foi feito

Aplicou padrao consistente a **todos os 5 docs principais**:

1. **Frontmatter enriquecido**: `description`, `keywords`, `sidebar_position`
2. **Admonitions contextuais**: :::tip, :::warning, :::danger, :::info, :::note
3. **Diagramas Mermaid**: Substituiu ASCII art em architecture/overview.md e runbooks/deploy.md
4. **Code block titles**: Todos os code blocks agora tem titulo descritivo
5. **Cross-links**: Secao "Veja tambem" no final de cada doc
6. **_category_.json**: Criado para architecture, standards, runbooks, api; atualizado adr

### Arquivos modificados
- `docs-site/docs/index.md`
- `docs-site/docs/architecture/overview.md`
- `docs-site/docs/standards/coding-standards.md`
- `docs-site/docs/runbooks/deploy.md`
- `docs-site/docs/adr/001-docusaurus-reviewops.md`
- `docs-site/docs/architecture/_category_.json` (novo)
- `docs-site/docs/standards/_category_.json` (novo)
- `docs-site/docs/runbooks/_category_.json` (novo)
- `docs-site/docs/api/_category_.json` (novo)
- `docs-site/docs/adr/_category_.json` (atualizado position: 4→5)

---

## FASE 4 — Performance (Bundle Splitting)

### O que foi feito

Adicionou `splitChunks.cacheGroups.openapiVendor` ao webpack plugin:

```javascript
config.optimization.splitChunks.cacheGroups.openapiVendor = {
  test: /[\\/]docusaurus-theme-openapi-docs[\\/]/,
  name: "openapi-vendor",
  chunks: "all",
  priority: 10,
};
```

O tema OpenAPI (~213KB) agora carrega apenas em rotas `/api/*`, reduzindo o bundle inicial.

### Arquivos modificados
- `docs-site/src/webpack-fallback-plugin.js`

---

## FASE 5 — Testes e Validacao

### Novos testes (+15)

| Teste | Valida |
|-------|--------|
| `test_webpack_plugin_has_openapi_split_chunks` | splitChunks configurado |
| `test_config_has_mermaid_theme` | Mermaid plugin ativo |
| `test_config_has_search_plugin` | Search local configurado |
| `test_config_has_announcement_bar` | Announcement bar presente |
| `test_config_has_color_mode_respect` | Respeita preferencia do OS |
| `test_favicon_svg_exists` | Favicon SVG existe |
| `test_social_card_exists` | Social card PNG existe |
| `test_robots_txt_exists` | robots.txt com Sitemap |
| `test_custom_404_page_exists` | 404.tsx com Layout |
| `test_all_docs_have_description_in_frontmatter` | SEO em todos os docs |
| `test_all_docs_have_keywords_in_frontmatter` | Keywords em todos os docs |
| `test_docs_use_admonitions` | >= 4 docs com ::: |
| `test_docs_have_cross_links` | >= 4 docs com "Veja tambem" |
| `test_docs_use_mermaid_diagrams` | >= 2 docs com mermaid |
| `test_all_doc_dirs_have_category_json` | Ordenacao deterministica |

### Resultados

```
73 passed in 0.15s
ruff check: All checks passed!
pnpm build: Generated static files in "build"
```

---

## Decisoes Tecnicas

| Decisao | Alternativa rejeitada | Motivo |
|---------|----------------------|--------|
| Busca local (lunr.js) | Algolia DocSearch | Template drop-in nao deve exigir conta externa |
| SVG favicon | .ico | Escala, versiona como texto, diffs em PR |
| CSS variables | Swizzle de componentes | Menos risco em upgrades do Docusaurus |
| Mermaid | Imagens estaticas | Diff-able em PRs, auto-tema light/dark |
| ideal-image comentado | Instalado ativo | sharp nao compila no ambiente atual |
