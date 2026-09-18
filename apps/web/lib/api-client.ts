import { apiBaseUrl } from "./api-base";
import { clearAccessToken, getAccessToken } from "./auth-token";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail.map((d) => d.msg).join("; ");
    }
  } catch {
    /* ignore */
  }
  return res.statusText || "Request failed";
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (auth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers });

  if (res.status === 401 && auth) {
    clearAccessToken();
  }

  if (!res.ok) {
    const detail = await parseError(res);
    throw new ApiError(detail, res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export type TokenResponse = { access_token: string; token_type: string };
export type UserOut = { id: string; email: string; roles: string[]; created_at: string };
export type KnowledgeBaseOut = {
  id: string;
  name: string;
  description: string | null;
  created_by: string | null;
  created_at: string;
};
export type DocumentOut = {
  id: string;
  kb_id: string;
  source: string;
  title: string | null;
  uri: string | null;
  mime_type: string | null;
  status: string;
  created_at: string;
};
export type DocumentContentOut = {
  id: string;
  kb_id: string;
  title: string | null;
  mime_type: string | null;
  content: string;
};
export type DocumentUploadOut = { document: DocumentOut; job_id: string };
export type IndexJobOut = {
  id: string;
  kb_id: string | null;
  document_id: string | null;
  job_type: string | null;
  state: string | null;
  error: string | null;
  stats: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};
export type CitationOut = {
  evidence_id: string;
  document_id: string | null;
  kb_id: string | null;
  title: string | null;
  uri: string | null;
  snippet: string | null;
  score: number | null;
  index: number | null;
};
export type QueryResponseOut = {
  answer: string;
  citations: CitationOut[];
  route: string;
  refuse_reason: string | null;
  trace_id: string;
};
export type ConnectorOut = {
  id: string;
  kb_id: string | null;
  type: string | null;
  enabled: boolean | null;
  cursor: string | null;
};
