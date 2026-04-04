// CONFIGURACAO DO PORTAL DOCUSAURUS
// Substitua os placeholders marcados com TODO antes de publicar.

import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import type * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";

const config: Config = {
  // TODO: Substitua pelo nome do seu portal
  title: "Engineering Docs",
  // TODO: Substitua pelo tagline da sua empresa/produto
  tagline: "Documentacao viva de produto, plataforma e operacao",
  favicon: "img/favicon.svg",

  // TODO: Substitua pelo dominio do GitHub Pages da sua org
  // Ex: "https://minha-org.github.io"
  url: "https://example.github.io",
  // TODO: Substitua pelo nome do repositorio (ou "/" se for org page)
  baseUrl: "/engineering-docs/",

  // TODO: Substitua pelo nome da organizacao no GitHub
  organizationName: "example",
  // TODO: Substitua pelo nome do repositorio no GitHub
  projectName: "engineering-docs",

  onBrokenLinks: "throw",
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: "throw",
    },
  },

  i18n: {
    defaultLocale: "pt-BR",
    locales: ["pt-BR"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          // Portal docs-first: raiz do site e a documentacao
          routeBasePath: "/",
          sidebarPath: "./sidebars.ts",
          // Plugin OpenAPI gera docs automaticamente
          docItemComponent: "@theme/ApiItem",
          // TODO: Substitua pela URL do seu repositorio
          editUrl: "https://github.com/example/repo/tree/main/docs-site/",
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
          // Versionamento sera configurado apos o primeiro docs:version.
          // O workflow docs-version-pr.yml cria automaticamente versioned_docs/
          // e versions.json quando uma tag e publicada.
          // Descomente o bloco abaixo apos a primeira release:
          // lastVersion: "current",
          // versions: {
          //   current: { label: "Next", path: "next", banner: "unreleased" },
          // },
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    // Plugin local: resolve fallback de modulos Node para postman-code-generators
    require.resolve("./src/webpack-fallback-plugin.js"),
    [
      "docusaurus-plugin-openapi-docs",
      {
        id: "api",
        docsPluginId: "classic",
        config: {
          core: {
            // Schema exportado automaticamente pelo scripts/export_openapi.py
            specPath: "openapi/openapi.json",
            outputDir: "docs/api/core",
            sidebarOptions: {
              groupPathsBy: "tag",
              sidebarCollapsible: true,
              sidebarCollapsed: true,
            },
          } satisfies OpenApiPlugin.Options,
        },
      },
    ],
    // Busca local offline — sem necessidade de conta Algolia
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        hashed: true,
        language: ["pt", "en"],
        indexBlog: false,
        docsRouteBasePath: "/",
      },
    ],
    // Para otimizacao de imagens, instale @docusaurus/plugin-ideal-image
    // e descomente a config abaixo (requer build nativo do sharp):
    // ["@docusaurus/plugin-ideal-image", { quality: 85, max: 1200, min: 400 }],
  ],

  themes: ["docusaurus-theme-openapi-docs", "@docusaurus/theme-mermaid"],

  themeConfig: {
    image: "img/social-card.png",

    // Respeita preferencia de dark/light mode do sistema
    colorMode: {
      respectPrefersColorScheme: true,
    },

    // Banner informativo — remova apos configurar os placeholders
    announcementBar: {
      id: "setup-notice",
      content:
        "Portal em construcao — substitua os <strong>placeholders TODO</strong> antes de publicar. Execute <code>make validate</code> para verificar.",
      backgroundColor: "#2e86ab",
      textColor: "#fff",
      isCloseable: true,
    },

    metadata: [
      { name: "keywords", content: "documentacao, API, arquitetura, engenharia" },
    ],

    navbar: {
      // TODO: Substitua pelo titulo do portal
      title: "Engineering Docs",
      items: [
        { to: "/", label: "Home", position: "left" },
        {
          to: "/architecture/overview",
          label: "Architecture",
          position: "left",
        },
        {
          to: "/standards/coding-standards",
          label: "Standards",
          position: "left",
        },
        { to: "/runbooks/deploy", label: "Runbooks", position: "left" },
        { to: "/api/core/api", label: "API", position: "left" },
        // Dropdown de versoes — aparece apos o primeiro freeze de versao
        { type: "docsVersionDropdown", position: "right" },
        {
          // TODO: Substitua pela URL do seu repositorio
          href: "https://github.com/example/repo",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Portal",
          items: [
            { label: "Architecture", to: "/architecture/overview" },
            { label: "Standards", to: "/standards/coding-standards" },
            { label: "Runbooks", to: "/runbooks/deploy" },
            { label: "API", to: "/api/core/api" },
          ],
        },
      ],
      // TODO: Substitua pelo nome da empresa
      copyright: `Copyright © ${new Date().getFullYear()} Example Corp`,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
