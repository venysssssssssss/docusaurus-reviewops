/**
 * Swizzled ApiLogo — ESM re-implementation of the upstream CommonJS component.
 *
 * Based on docusaurus-theme-openapi-docs v4.7.1 ApiLogo/index.tsx
 * Copyright (c) Palo Alto Networks — MIT License
 */

import React from "react";

import { useColorMode } from "@docusaurus/theme-common";
import useBaseUrl from "@docusaurus/useBaseUrl";
import ThemedImage from "@theme/ThemedImage";

export default function ApiLogo({ logo, darkLogo }) {
  const { colorMode } = useColorMode();

  const altText = () => {
    if (colorMode === "dark") {
      return darkLogo?.altText ?? logo?.altText;
    }
    return logo?.altText;
  };

  const lightLogoUrl = useBaseUrl(logo?.url);
  const darkLogoUrl = useBaseUrl(darkLogo?.url);

  if (logo && darkLogo) {
    return (
      <ThemedImage
        alt={altText()}
        sources={{ light: lightLogoUrl, dark: darkLogoUrl }}
        className="openapi__logo"
      />
    );
  }

  if (logo || darkLogo) {
    return (
      <ThemedImage
        alt={altText()}
        sources={{
          light: lightLogoUrl ?? darkLogoUrl,
          dark: lightLogoUrl ?? darkLogoUrl,
        }}
        className="openapi__logo"
      />
    );
  }

  return undefined;
}
