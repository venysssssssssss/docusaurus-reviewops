/**
 * Swizzled Export — ESM re-implementation of the upstream CommonJS component.
 *
 * Based on docusaurus-theme-openapi-docs v4.7.1 ApiExplorer/Export/index.tsx
 * Copyright (c) Palo Alto Networks — MIT License
 */

import React from "react";

import { saveAs } from "file-saver";

function saveFile(url) {
  let fileName;
  if (url.endsWith("json") || url.endsWith("yaml") || url.endsWith("yml")) {
    fileName = url.substring(url.lastIndexOf("/") + 1);
  }
  saveAs(url, fileName ? fileName : "openapi.txt");
}

export default function Export({ url }) {
  return (
    <div
      style={{ float: "right" }}
      className="dropdown dropdown--hoverable dropdown--right"
    >
      <button className="export-button button button--sm button--secondary">
        Export
      </button>
      <ul className="export-dropdown dropdown__menu">
        <li>
          <a
            onClick={(e) => {
              e.preventDefault();
              saveFile(url);
            }}
            className="dropdown__link"
            href={url}
          >
            OpenAPI Spec
          </a>
        </li>
      </ul>
    </div>
  );
}
