// API 基础配置
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 常用 API 端点
export const API_ENDPOINTS = {
  login: `${API_BASE}/api/login/`,
  signup: `${API_BASE}/api/signup/`,
  logout: `${API_BASE}/logout/`,
  conversations: `${API_BASE}/conversations/`,
  askAi: `${API_BASE}/ask_ai/`,
  addPdf: `${API_BASE}/add_pdf/`,
  listPdfs: `${API_BASE}/list_pdfs/`,
  authStatus: `${API_BASE}/auth_status/`,
} as const;
