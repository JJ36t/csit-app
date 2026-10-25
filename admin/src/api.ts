// عميل الـAPI للوحة التحكم: توكن في localStorage + معالجة أخطاء عربية موحدة.

export interface ApiErrorPayload {
  code: string;
  message_ar: string;
  details?: unknown;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(payload: ApiErrorPayload, status = 0) {
    super(payload.message_ar);
    this.code = payload.code;
    this.status = status;
    this.details = payload.details;
  }
}

export interface AdminUser {
  university_id: string;
  full_name_ar: string;
  role: string;
  must_change_password: boolean;
}

const TOKEN_KEY = 'csit_token';
const DEVICE_KEY = 'csit_device';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function deviceFingerprint(): string {
  let id = localStorage.getItem(DEVICE_KEY);
  if (!id) {
    id = `web-${crypto.randomUUID()}`;
    localStorage.setItem(DEVICE_KEY, id);
  }
  return id;
}

async function rawRequest(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  return fetch(path, { ...options, headers });
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await rawRequest(path, options);
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const payload = (data ?? {
      code: 'unknown_error',
      message_ar: 'تعذّر تنفيذ الطلب',
    }) as ApiErrorPayload;
    throw new ApiError(payload, res.status);
  }
  return data as T;
}

export interface LoginResponse {
  access_token: string;
  expires_in: number;
  refresh_token: string;
  user: AdminUser;
}

export async function login(universityId: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({
      university_id: universityId,
      password,
      device: { fingerprint: deviceFingerprint(), model: 'Web Admin', platform: 'web' },
    }),
  });
}

export interface ImportIssue {
  row: number;
  column: string;
  code: string;
  message_ar: string;
}

export interface ImportResult {
  dry_run: boolean;
  rows_total: number;
  rows_valid: number;
  rows_invalid: number;
  created_count: number;
  created: { university_id: string; full_name_ar: string; initial_password?: string }[];
  groups_created: string[];
  errors: ImportIssue[];
  errors_truncated: boolean;
}

export async function importStudents(file: File, dryRun: boolean): Promise<ImportResult> {
  const form = new FormData();
  form.append('file', file);
  return request<ImportResult>(`/api/v1/admin/students/import?dry_run=${dryRun}`, {
    method: 'POST',
    body: form,
  });
}

export interface StudentRow {
  university_id: string;
  full_name_ar: string;
  department_code: string;
  department_name_ar: string;
  stage: number;
  study_type: string;
  group_name: string | null;
  status: string;
  email: string | null;
  phone: string | null;
}

export interface StudentList {
  total: number;
  page: number;
  limit: number;
  items: StudentRow[];
}

export async function listStudents(params: Record<string, string | number | undefined>): Promise<StudentList> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<StudentList>(`/api/v1/admin/students?${qs.toString()}`);
}

export async function downloadTemplate(): Promise<void> {
  const res = await rawRequest('/api/v1/admin/students/template');
  if (!res.ok) {
    throw new ApiError({ code: 'template_failed', message_ar: 'تعذّر تنزيل القالب' }, res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'students-template.xlsx';
  anchor.click();
  URL.revokeObjectURL(url);
}
