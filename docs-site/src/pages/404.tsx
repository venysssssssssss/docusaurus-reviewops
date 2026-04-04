import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";

export default function NotFound(): React.JSX.Element {
  return (
    <Layout title="Pagina nao encontrada">
      <div className="not-found-container">
        <h1>404</h1>
        <p>Pagina nao encontrada. Verifique o endereco ou navegue pelo menu.</p>
        <Link className="button button--primary button--lg" to="/">
          Voltar para Home
        </Link>
      </div>
    </Layout>
  );
}
