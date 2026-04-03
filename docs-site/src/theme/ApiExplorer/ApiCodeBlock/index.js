import React, { isValidElement } from "react";

import CodeBlock from "@theme/CodeBlock";

function maybeStringifyChildren(children) {
  if (React.Children.toArray(children).some((child) => isValidElement(child))) {
    return children;
  }

  return Array.isArray(children) ? children.join("") : children;
}

export default function ApiCodeBlock({ children, ...props }) {
  const content = maybeStringifyChildren(children);

  if (typeof content !== "string") {
    return <div {...props}>{content}</div>;
  }

  return <CodeBlock {...props}>{content}</CodeBlock>;
}
