// API 全局响应类型

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

// AI 对话
export interface ChatRequest {
  messages: { role: string; content: string }[];
  system_prompt?: string;
  max_iterations?: number;
  permission_name?: string;
  tool_names?: string[];
  llm_kwargs?: Record<string, any>;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking?: string;
}

export interface ChatResponse {
  messages: { role: string; content: string }[];
}

// 管理接口
export interface InitDbResponse {
  message: string;
}

export interface BackupDbResponse {
  message: string;
}

export interface ResetDbResponse {
  message: string;
}

export interface RestoreDbResponse {
  message: string;
}

export interface ListBackupsResponse {
  backups: string[];
}

// AI Permission
export interface AIPermissionReadRequest {
  view: Record<string, unknown>;
}

export interface AIPermissionRequest {
  read_view: Record<string, unknown>;
  write_view: Record<string, unknown>;
}

// Notebook 元信息
export interface NotebookInfo {
  table_name: string;
  label: string;
  description: string;
  entry_count?: number;
}
