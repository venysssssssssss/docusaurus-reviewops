import React from "react";

function getResponseCodes(item) {
  return Object.keys(item?.responses ?? {});
}

function getServerUrls(item) {
  return (item?.servers ?? [])
    .map((server) => server?.url)
    .filter((url) => typeof url === "string" && url.length > 0);
}

function getSecuritySchemeKeys(item) {
  return Object.keys(item?.securitySchemes ?? {});
}

export default function ApiExplorer({ item }) {
  const responseCodes = getResponseCodes(item);
  const serverUrls = getServerUrls(item);
  const securitySchemes = getSecuritySchemeKeys(item);

  return (
    <section className="openapi-explorer__container">
      <div className="theme-api-markdown">
        <h2>API Explorer Preview</h2>
        <p>
          The interactive request console is disabled in this local preview to
          avoid an upstream browser-bundle issue in the OpenAPI theme.
        </p>

        <dl>
          <dt>Method</dt>
          <dd>
            <code>{item?.method ?? "unknown"}</code>
          </dd>

          <dt>Path</dt>
          <dd>
            <code>{item?.path ?? "/"}</code>
          </dd>

          {item?.summary ? (
            <>
              <dt>Summary</dt>
              <dd>{item.summary}</dd>
            </>
          ) : null}

          {item?.operationId ? (
            <>
              <dt>Operation ID</dt>
              <dd>
                <code>{item.operationId}</code>
              </dd>
            </>
          ) : null}

          <dt>Response Codes</dt>
          <dd>{responseCodes.length > 0 ? responseCodes.join(", ") : "None"}</dd>

          <dt>Servers</dt>
          <dd>{serverUrls.length > 0 ? serverUrls.join(", ") : "None"}</dd>

          <dt>Security Schemes</dt>
          <dd>
            {securitySchemes.length > 0 ? securitySchemes.join(", ") : "None"}
          </dd>
        </dl>
      </div>
    </section>
  );
}
