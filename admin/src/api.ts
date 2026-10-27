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

export async function downloadFile(path: string, filename: string): Promise<void> {
  const res = await rawRequest(path);
  if (!res.ok) {
    let payload: ApiErrorPayload = { code: 'download_failed', message_ar: 'تعذّر تنزيل الملف' };
    try {
      const text = await res.text();
      if (text) payload = JSON.parse(text) as ApiErrorPayload;
    } catch {
      // لا محتوى JSON — نُبقي الرسالة الافتراضية
    }
    throw new ApiError(payload, res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadTemplate(): Promise<void> {
  await downloadFile('/api/v1/admin/students/template', 'students-template.xlsx');
}

// ----------------------------- الأقسام والمواد -----------------------------

export interface Department {
  id: string;
  code: string;
  name_ar: string;
  name_en: string;
}

export async function listDepartments(): Promise<Department[]> {
  return request<Department[]>('/api/v1/departments');
}

export interface Offering {
  offering_id: string;
  course_code: string;
  course_name_ar: string;
  kind: string;
  stage: number;
  group_name: string;
  study_type: string;
  instructor_name_ar: string | null;
}

export async function listOfferings(): Promise<{ items: Offering[] }> {
  return request<{ items: Offering[] }>('/api/v1/offerings');
}

// ----------------------------- الجدول -----------------------------

export interface TimetableSession {
  session_id: string;
  slot_id: string | null;
  offering_id: string;
  date: string;
  starts_at: string;
  ends_at: string;
  course_code: string;
  course_name_ar: string;
  kind: string;
  room: string | null;
  status: string;
}

export async function listTimetable(
  from: string,
  to: string,
): Promise<{ items: TimetableSession[] }> {
  return request<{ items: TimetableSession[] }>(
    `/api/v1/timetable?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
  );
}

export interface TimetableChangeRow {
  change_id: string;
  date: string;
  type: string;
  course_name_ar: string;
  new_start: string | null;
  reason: string | null;
}

export async function listTimetableChanges(
  from: string,
  to: string,
): Promise<{ items: TimetableChangeRow[] }> {
  return request<{ items: TimetableChangeRow[] }>(
    `/api/v1/timetable/changes?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
  );
}

export interface Room {
  room_id: string;
  name: string;
  building: string | null;
  lat: number | null;
  lng: number | null;
  radius_m: number | null;
}

export async function listRooms(): Promise<{ items: Room[] }> {
  return request<{ items: Room[] }>('/api/v1/admin/timetable/rooms');
}

export interface RoomInput {
  name: string;
  building?: string | null;
  lat?: number | null;
  lng?: number | null;
  radius_m?: number | null;
}

export async function createRoom(body: RoomInput): Promise<{ room_id: string; name: string }> {
  return request<{ room_id: string; name: string }>('/api/v1/admin/timetable/rooms', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export interface WeeklySlot {
  slot_id: string;
  offering_id: string;
  course_code: string;
  course_name_ar: string;
  group_name: string;
  stage: number;
  study_type: string;
  instructor_name_ar: string | null;
  weekday: number;
  start_time: string;
  end_time: string;
  room_id: string | null;
  room_name: string | null;
  kind: string;
}

export async function listSlots(offeringId?: string): Promise<{ items: WeeklySlot[] }> {
  const qs = offeringId ? `?offering_id=${encodeURIComponent(offeringId)}` : '';
  return request<{ items: WeeklySlot[] }>(`/api/v1/admin/timetable/slots${qs}`);
}

export interface SlotInput {
  offering_id: string;
  weekday: number;
  start_time: string;
  end_time: string;
  room_id?: string | null;
  kind: string;
}

export async function createSlot(
  body: SlotInput,
): Promise<{ slot_id: string; sessions_created: number }> {
  return request<{ slot_id: string; sessions_created: number }>(
    '/api/v1/admin/timetable/slots',
    { method: 'POST', body: JSON.stringify(body) },
  );
}

export interface ChangeInput {
  slot_id: string;
  date: string;
  type: string;
  new_start?: string | null;
  reason?: string | null;
}

export async function createChange(
  body: ChangeInput,
): Promise<{ change_id: string; type: string }> {
  return request<{ change_id: string; type: string }>('/api/v1/admin/timetable/changes', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ----------------------------- الدرجات -----------------------------

export interface Assessment {
  assessment_id: string;
  offering_id: string;
  name: string;
  kind: string;
  max_score: number;
  weight: number;
  is_published: boolean;
}

export interface StudentGradeRow {
  student_id: string;
  university_id: string;
  full_name_ar: string;
  scores: Record<string, number>;
  weighted_total: number;
  weight_sum: number;
}

export interface OfferingGrades {
  offering_id: string;
  course_code: string;
  course_name_ar: string;
  assessments: Assessment[];
  students: StudentGradeRow[];
}

export async function getOfferingGrades(offeringId: string): Promise<OfferingGrades> {
  return request<OfferingGrades>(`/api/v1/offerings/${offeringId}/grades`);
}

export interface AssessmentInput {
  offering_id: string;
  name: string;
  kind: string;
  max_score: number;
  weight: number;
}

export async function createAssessment(body: AssessmentInput): Promise<Assessment> {
  return request<Assessment>('/api/v1/assessments', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function deleteAssessment(id: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/api/v1/assessments/${id}`, { method: 'DELETE' });
}

export async function saveGrades(
  assessmentId: string,
  rows: { student_id: string; score: number }[],
): Promise<{ created: number; updated: number; unchanged: number }> {
  return request<{ created: number; updated: number; unchanged: number }>(
    `/api/v1/assessments/${assessmentId}/grades`,
    { method: 'POST', body: JSON.stringify({ rows }) },
  );
}

export async function publishAssessment(
  id: string,
): Promise<{ is_published: boolean; notified: number }> {
  return request<{ is_published: boolean; notified: number }>(
    `/api/v1/assessments/${id}/publish`,
    { method: 'POST' },
  );
}

export async function downloadGrades(offeringId: string, courseCode: string): Promise<void> {
  await downloadFile(
    `/api/v1/offerings/${offeringId}/grades/export`,
    `grades-${courseCode.replace(/\s+/g, '_')}.xlsx`,
  );
}

// ----------------------------- المستخدمون -----------------------------

export interface AdminUserRow {
  user_id: string;
  university_id: string;
  full_name_ar: string;
  role: string;
  status: string;
  must_change_password: boolean;
  department_code: string | null;
  department_name_ar: string | null;
  group_name: string | null;
  device_status: 'active' | 'none';
}

export interface AdminUserList {
  total: number;
  page: number;
  limit: number;
  items: AdminUserRow[];
}

export async function listAdminUsers(
  params: Record<string, string | number | undefined>,
): Promise<AdminUserList> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<AdminUserList>(`/api/v1/admin/users?${qs.toString()}`);
}

export async function resetUserDevice(
  universityId: string,
): Promise<{ ok: boolean; devices_revoked: number; sessions_revoked: number }> {
  return request<{ ok: boolean; devices_revoked: number; sessions_revoked: number }>(
    `/api/v1/admin/users/${encodeURIComponent(universityId)}/device/reset`,
    { method: 'POST' },
  );
}

export async function resetUserPassword(
  universityId: string,
): Promise<{ ok: boolean; temporary_password: string; sessions_revoked: number }> {
  return request<{ ok: boolean; temporary_password: string; sessions_revoked: number }>(
    `/api/v1/admin/users/${encodeURIComponent(universityId)}/reset-password`,
    { method: 'POST' },
  );
}

// ----------------------------- الإعلانات -----------------------------

export interface AdminAnnouncement {
  announcement_id: string;
  scope: string;
  scope_id: string | null;
  stage: number | null;
  title: string;
  body: string;
  priority: string;
  pinned: boolean;
  publish_at: string | null;
  expires_at: string | null;
  created_at: string | null;
  status: 'scheduled' | 'active' | 'expired';
}

export async function listAdminAnnouncements(): Promise<{ items: AdminAnnouncement[] }> {
  return request<{ items: AdminAnnouncement[] }>('/api/v1/admin/announcements');
}

export interface AnnouncementInput {
  scope: string;
  scope_id?: string | null;
  stage?: number | null;
  title: string;
  body: string;
  priority?: string;
  pinned?: boolean;
  publish_at?: string | null;
  expires_at?: string | null;
}

export async function createAnnouncement(body: AnnouncementInput): Promise<AdminAnnouncement> {
  return request<AdminAnnouncement>('/api/v1/admin/announcements', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function deleteAnnouncement(
  id: string,
): Promise<{ announcement_id: string; deleted: boolean }> {
  return request<{ announcement_id: string; deleted: boolean }>(
    `/api/v1/admin/announcements/${id}`,
    { method: 'DELETE' },
  );
}

// ----------------------------- سجل التدقيق -----------------------------

export interface AuditRow {
  audit_id: string;
  created_at: string | null;
  actor_university_id: string | null;
  actor_name_ar: string | null;
  action: string;
  entity: string;
  entity_id: string;
  ip: string | null;
  before?: unknown;
  after?: unknown;
}

export interface AuditList {
  total: number;
  page: number;
  limit: number;
  items: AuditRow[];
}

export async function listAudit(
  params: Record<string, string | number | undefined>,
): Promise<AuditList> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<AuditList>(`/api/v1/admin/audit?${qs.toString()}`);
}

// ----------------------------- لوحة الملخص -----------------------------

export interface OverviewData {
  students: {
    total: number;
    by_department: { code: string; name_ar: string; count: number }[];
  };
  today: { sessions: number; present: number; late: number; absent: number };
  grades: { published: number; drafts: number };
  announcements: { active: number; scheduled: number };
}

export async function getOverview(): Promise<OverviewData> {
  return request<OverviewData>('/api/v1/admin/overview');
}

// ----------------------------- الأكاديمية (N8) -----------------------------

export interface TermInfo {
  term_id: string;
  name: string;
  year_label: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
}

export async function listTerms(): Promise<{ items: TermInfo[] }> {
  return request<{ items: TermInfo[] }>('/api/v1/admin/terms');
}

export interface AdminGroup {
  group_id: string;
  department_id: string;
  department_code: string | null;
  department_name_ar: string | null;
  stage: number;
  name: string;
  study_type: string;
  term_id: string;
  term_name: string | null;
}

export async function listGroups(params: Record<string, string | number | undefined> = {}): Promise<{
  items: AdminGroup[];
}> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<{ items: AdminGroup[] }>(`/api/v1/admin/groups?${qs.toString()}`);
}

export interface GroupInput {
  department_id: string;
  stage: number;
  name: string;
  study_type: string;
  term_id: string;
}

export async function createGroup(body: GroupInput): Promise<AdminGroup> {
  return request<AdminGroup>('/api/v1/admin/groups', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export interface CourseInfo {
  course_id: string;
  code: string;
  name_ar: string;
  department_id: string;
  stage: number;
  units: number;
  kind: string;
}

export async function listCourses(
  params: Record<string, string | number | undefined> = {},
): Promise<{ items: CourseInfo[] }> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<{ items: CourseInfo[] }>(`/api/v1/admin/courses?${qs.toString()}`);
}

export interface AdminOffering {
  offering_id: string;
  course_id: string;
  course_code: string;
  course_name_ar: string;
  group_id: string;
  group_name: string;
  stage: number;
  study_type: string;
  kind: string;
  instructor_id: string | null;
  instructor_name_ar: string | null;
  enrolled: number;
}

export async function listAdminOfferings(
  params: Record<string, string | number | undefined> = {},
): Promise<{ items: AdminOffering[] }> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') qs.set(key, String(value));
  });
  return request<{ items: AdminOffering[] }>(`/api/v1/admin/offerings?${qs.toString()}`);
}

export interface OfferingInput {
  course_id: string;
  group_id: string;
  instructor_id?: string | null;
  session_kind?: string | null;
}

export async function createOffering(body: OfferingInput): Promise<AdminOffering> {
  return request<AdminOffering>('/api/v1/admin/offerings', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function downloadAttendanceReport(
  offeringId: string,
  courseCode: string,
): Promise<void> {
  await downloadFile(
    `/api/v1/admin/reports/attendance?offering_id=${encodeURIComponent(offeringId)}&format=csv`,
    `attendance-${courseCode.replace(/\s+/g, '_')}.csv`,
  );
}

export async function downloadGradesReport(
  offeringId: string,
  courseCode: string,
): Promise<void> {
  await downloadFile(
    `/api/v1/admin/reports/grades?offering_id=${encodeURIComponent(offeringId)}&format=csv`,
    `grades-report-${courseCode.replace(/\s+/g, '_')}.csv`,
  );
}
// ----------------------------- الأعذار (N8) -----------------------------

export interface AdminExcuse {
  excuse_id: string;
  session_id: string;
  session_date: string;
  course_code: string;
  course_name_ar: string;
  student_name_ar: string | null;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  review_note: string | null;
  reviewed_at: string | null;
  attachment: { file_id: string; name: string; download_url: string } | null;
}

export async function listAdminExcuses(status = 'pending'): Promise<{
  items: AdminExcuse[];
  pending_total: number;
}> {
  return request<{ items: AdminExcuse[]; pending_total: number }>(
    `/api/v1/admin/excuses?status=${encodeURIComponent(status)}`,
  );
}

export async function reviewExcuse(
  excuseId: string,
  approve: boolean,
  note?: string,
): Promise<AdminExcuse> {
  return request<AdminExcuse>(`/api/v1/admin/excuses/${excuseId}/review`, {
    method: 'POST',
    body: JSON.stringify({ status: approve ? 'approved' : 'rejected', note: note || null }),
  });
}

// ----------------------------- الطلبات (N8) -----------------------------

export interface AdminRequestRow {
  request_id: string;
  category: string;
  category_label: string;
  subject: string;
  status: string;
  assigned_to: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminRequestMessage {
  message_id: string;
  sender_id: string;
  body: string;
  created_at: string | null;
}

export interface AdminRequestDetail extends AdminRequestRow {
  messages: AdminRequestMessage[];
}

export async function listAdminRequests(status?: string): Promise<{ items: AdminRequestRow[] }> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return request<{ items: AdminRequestRow[] }>(`/api/v1/requests${qs}`);
}

export async function getAdminRequest(id: string): Promise<AdminRequestDetail> {
  return request<AdminRequestDetail>(`/api/v1/requests/${id}`);
}

export async function replyAdminRequest(id: string, body: string): Promise<AdminRequestDetail> {
  return request<AdminRequestDetail>(`/api/v1/requests/${id}/messages`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  });
}

export async function updateAdminRequest(
  id: string,
  patch: { status?: string; assigned_to?: string },
): Promise<AdminRequestDetail> {
  return request<AdminRequestDetail>(`/api/v1/admin/requests/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}

export async function resetUserTotp(
  universityId: string,
): Promise<{ ok: boolean; was_enabled: boolean }> {
  return request<{ ok: boolean; was_enabled: boolean }>(
    `/api/v1/admin/users/${encodeURIComponent(universityId)}/2fa/reset`,
    { method: 'POST' },
  );
}