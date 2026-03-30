// 📍 LOCATION: free-space/frontend/packages/types/src/api.ts
//
// API envelope types — mirror backend's error format exactly
// Backend ref: core/exceptions/base.py  →  { error_code, message, details }

// ─── Success envelope ────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
    results: T[];
    next: string | null;      // cursor token for next page
    previous: string | null;  // cursor token for previous page
    count: number;
  }
  
  // ─── Error envelope — mirrors BaseAPIException ────────────────────────────────
  export interface ApiError {
    error_code: string;   // e.g. "USER_NOT_FOUND", "VALIDATION_ERROR"
    message: string;      // human-readable
    details: Record<string, unknown>; // field-level errors or extra context
  }
  
  // ─── HTTP status categories ───────────────────────────────────────────────────
  export type ApiErrorCode =
    | 'VALIDATION_ERROR'
    | 'AUTHENTICATION_REQUIRED'
    | 'PERMISSION_DENIED'
    | 'NOT_FOUND'
    | 'RATE_LIMITED'
    | 'ACCOUNT_SUSPENDED'
    | 'EMAIL_NOT_VERIFIED'
    | 'DUPLICATE_FOLLOW'
    | 'CANNOT_FOLLOW_SELF'
    | 'BLOCKED_BY_USER'
    | 'CONTENT_TOO_LONG'
    | 'MEDIA_UPLOAD_FAILED'
    | 'INVALID_MEDIA_TYPE'
    | 'SERVER_ERROR';
  
  // ─── Typed API error for use in catch blocks ─────────────────────────────────
  export class ApiException extends Error {
    public readonly error_code: ApiErrorCode | string;
    public readonly details: Record<string, unknown>;
    public readonly status: number;
  
    constructor(error: ApiError, status: number) {
      super(error.message);
      this.name = 'ApiException';
      this.error_code = error.error_code;
      this.details = error.details;
      this.status = status;
    }
  
    /** True if this is a field-level validation error */
    isValidationError(): boolean {
      return this.error_code === 'VALIDATION_ERROR';
    }
  
    /** Returns field errors as { fieldName: errorMessage } */
    getFieldErrors(): Record<string, string> {
      const raw = this.details as Record<string, string[] | string>;
      return Object.fromEntries(
        Object.entries(raw).map(([k, v]) => [k, Array.isArray(v) ? v[0] ?? '' : v]),
      );
    }
  }
  