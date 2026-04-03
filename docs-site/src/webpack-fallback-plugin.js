// Plugin Docusaurus para adicionar fallback do webpack para modulos Node-only
// usados por postman-code-generators (dependencia do docusaurus-plugin-openapi-docs).
// Ref: https://webpack.js.org/configuration/resolve/#resolvefallback

module.exports = function webpackFallbackPlugin(_context, _options) {
  const openApiThemeCommonJsPattern =
    /[\\/]docusaurus-theme-openapi-docs[\\/]lib[\\/].*\.js$/;

  return {
    name: "webpack-fallback-plugin",
    configureWebpack(_config, isServer) {
      if (isServer) return {};
      return {
        resolve: {
          fallback: {
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
          },
        },
        module: {
          rules: [
            {
              // The OpenAPI theme ships client files in CommonJS under lib/.
              // In dev, webpack can interpret them as ESM and leave bare
              // `exports` references in the browser bundle.
              test: openApiThemeCommonJsPattern,
              type: "javascript/auto",
            },
          ],
        },
      };
    },
  };
};
