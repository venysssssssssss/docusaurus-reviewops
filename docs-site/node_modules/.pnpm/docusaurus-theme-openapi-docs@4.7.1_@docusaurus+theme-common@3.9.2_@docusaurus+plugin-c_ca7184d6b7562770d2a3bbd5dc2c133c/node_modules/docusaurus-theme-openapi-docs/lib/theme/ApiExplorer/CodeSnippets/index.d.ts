import React from "react";
import * as sdk from "postman-collection";
import { CodeSample, Language } from "./code-snippets-types";
export declare const languageSet: Language[];
export interface Props {
    postman: sdk.Request;
    codeSamples: CodeSample[];
    maskCredentials?: boolean;
}
declare function CodeSnippets({ postman, codeSamples, maskCredentials: propMaskCredentials, }: Props): React.JSX.Element | null;
export default CodeSnippets;
