import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import type * as OpenApiPlugin from "docusaurus-plugin-openapi-docs";

const config: Config = {
  title: "docusaurus-reviewops",
  tagline: "Documentacao viva de produto, plataforma e operacao",
  favicon: "img/favicon.svg",

  url: "https://venysssssssssss.github.io",
  baseUrl: "/docusaurus-reviewops/",

  organizationName: "venysssssssssss",
  projectName: "docusaurus-reviewops",

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
          editUrl:
            "https://github.com/venysssssssssss/docusaurus-reviewops/tree/master/docs-site/",
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
  ],

  themes: ["docusaurus-theme-openapi-docs", "@docusaurus/theme-mermaid"],

  themeConfig: {
    image: "img/social-card.png",

    // Respeita preferencia de dark/light mode do sistema
    colorMode: {
      respectPrefersColorScheme: true,
    },

    metadata: [
      { name: "keywords", content: "documentacao, API, arquitetura, engenharia" },
    ],

    navbar: {
      title: "docusaurus-reviewops",
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
          href: "https://github.com/venysssssssssss/docusaurus-reviewops",
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
        {
          title: "Repositorio",
          items: [
            {
              label: "GitHub",
              href: "https://github.com/venysssssssssss/docusaurus-reviewops",
            },
            {
              label: "Issues",
              href: "https://github.com/venysssssssssss/docusaurus-reviewops/issues",
            },
            {
              label: "Changelog",
              to: "https://github.com/venysssssssssss/docusaurus-reviewops/blob/master/CHANGELOG.md",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} venysssssssssss — MIT License`,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
