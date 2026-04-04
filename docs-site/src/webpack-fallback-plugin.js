// Plugin Docusaurus: resolve fallback para modulos Node-only usados por
// postman-code-generators (dep transitiva do docusaurus-plugin-openapi-docs)
// e forcamento de CommonJS para arquivos do theme que usam `exports`.
//
// Ref: https://webpack.js.org/configuration/resolve/#resolvefallback

const NODE_FALLBACKS = {
  path: false,
  fs: false,
  os: false,
  crypto: false,
  stream: false,
  buffer: false,
  http: false,
  https: false,
  url: false,
  assert: false,
  util: false,
  querystring: false,
  zlib: false,
  net: false,
  tls: false,
};

// All lib/ files from the OpenAPI theme are compiled CommonJS (have `exports.`).
// Webpack's default config treats them as ESM → "exports is not defined".
const OPENAPI_THEME_CJS_PATTERN =
  /[\\/]docusaurus-theme-openapi-docs[\\/]lib[\\/]/;

module.exports = function webpackFallbackPlugin() {
  return {
    name: "webpack-fallback-plugin",

    configureWebpack(config, isServer) {
      // --- Force CommonJS for openapi theme lib/ files ---
      // Applied to BOTH client and server builds: the theme's compiled
      // lib/ files use CommonJS `exports` but webpack treats them as ESM,
      // causing "exports is not defined" (client) or "Cannot find module"
      // (server SSG). We mutate config directly because webpack-merge
      // appends rules and the default JS rule takes priority.
      config.module = config.module || {};
      config.module.rules = config.module.rules || [];
      config.module.rules.unshift({
        test: OPENAPI_THEME_CJS_PATTERN,
        type: "javascript/auto",
      });

      // Client-only optimizations.
      if (!isServer) {
        // Resolve fallbacks (Node modules → false in browser).
        config.resolve = config.resolve || {};
        config.resolve.fallback = {
          ...config.resolve.fallback,
          ...NODE_FALLBACKS,
        };

        // Split OpenAPI theme into its own chunk so it only loads on /api/* routes.
        config.optimization = config.optimization || {};
        config.optimization.splitChunks = config.optimization.splitChunks || {};
        const sc = config.optimization.splitChunks;
        sc.cacheGroups = sc.cacheGroups || {};
        sc.cacheGroups.openapiVendor = {
          test: /[\\/]docusaurus-theme-openapi-docs[\\/]/,
          name: "openapi-vendor",
          chunks: "all",
          priority: 10,
        };
      }

      return {};
    },
  };
};
