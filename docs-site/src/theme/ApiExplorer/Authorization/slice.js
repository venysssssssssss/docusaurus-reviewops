import { createSlice } from "@reduxjs/toolkit";
import { createStorage, hashArray } from "@theme/ApiExplorer/storage-utils";

function getAuthDataKeys(security) {
  if (security.type === "http" && security.scheme === "bearer") {
    return ["token"];
  }

  if (security.type === "oauth2") {
    return ["token"];
  }

  if (security.type === "http" && security.scheme === "basic") {
    return ["username", "password"];
  }

  if (security.type === "apiKey") {
    return ["apiKey"];
  }

  return [];
}

export function createAuth({ security, securitySchemes, options: opts }) {
  const storage = createStorage(opts?.authPersistence ?? "sessionStorage");

  const data = {};
  const options = {};

  for (const option of security ?? []) {
    const id = Object.keys(option).join(" and ");

    for (const [schemeID, scopes] of Object.entries(option)) {
      const scheme = securitySchemes?.[schemeID];
      if (!scheme) {
        continue;
      }

      options[id] ??= [];
      data[schemeID] ??= {};

      for (const key of getAuthDataKeys(scheme)) {
        let persisted;
        try {
          persisted = JSON.parse(storage.getItem(schemeID) ?? "")?.[key];
        } catch {
          persisted = undefined;
        }

        data[schemeID][key] = persisted;
      }

      options[id].push({
        ...scheme,
        key: schemeID,
        scopes,
      });
    }
  }

  let persisted;
  try {
    persisted = storage.getItem(hashArray(Object.keys(options))) ?? undefined;
  } catch {
    persisted = undefined;
  }

  return {
    data,
    options,
    selected: persisted ?? Object.keys(options)[0],
  };
}

const initialState = {
  data: {},
  options: {},
};

export const slice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuthData: (state, action) => {
      const { scheme, key, value } = action.payload;
      state.data[scheme][key] = value;
    },
    setSelectedAuth: (state, action) => {
      state.selected = action.payload;
    },
  },
});

export const { setAuthData, setSelectedAuth } = slice.actions;

export default slice.reducer;
