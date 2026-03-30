// 📍 LOCATION: free-space/frontend/packages/types/src/__tests__/api.test.ts
//
// Tests for ApiException — the error class used throughout the frontend.

import { describe, it, expect } from 'vitest';
import { ApiException } from '../api';

describe('ApiException', () => {
  it('stores error_code, message, status, and details', () => {
    const exception = new ApiException(
      { error_code: 'NOT_FOUND', message: 'User not found', details: {} },
      404,
    );

    expect(exception.error_code).toBe('NOT_FOUND');
    expect(exception.message).toBe('User not found');
    expect(exception.status).toBe(404);
    expect(exception.name).toBe('ApiException');
  });

  it('isValidationError returns true for VALIDATION_ERROR code', () => {
    const exception = new ApiException(
      { error_code: 'VALIDATION_ERROR', message: 'Validation failed', details: {} },
      400,
    );
    expect(exception.isValidationError()).toBe(true);
  });

  it('isValidationError returns false for other error codes', () => {
    const exception = new ApiException(
      { error_code: 'NOT_FOUND', message: 'Not found', details: {} },
      404,
    );
    expect(exception.isValidationError()).toBe(false);
  });

  it('getFieldErrors flattens array field errors to first message', () => {
    const exception = new ApiException(
      {
        error_code: 'VALIDATION_ERROR',
        message:    'Validation failed',
        details: {
          username: ['This username is taken.', 'Try another one.'],
          email:    ['Enter a valid email address.'],
        },
      },
      400,
    );

    const fieldErrors = exception.getFieldErrors();

    expect(fieldErrors.username).toBe('This username is taken.');
    expect(fieldErrors.email).toBe('Enter a valid email address.');
  });

  it('getFieldErrors handles string field errors (non-array)', () => {
    const exception = new ApiException(
      {
        error_code: 'VALIDATION_ERROR',
        message:    'Validation failed',
        details:    { password: 'Password is too weak.' },
      },
      400,
    );

    expect(exception.getFieldErrors().password).toBe('Password is too weak.');
  });

  it('is instanceof Error', () => {
    const exception = new ApiException(
      { error_code: 'SERVER_ERROR', message: 'Internal error', details: {} },
      500,
    );
    expect(exception).toBeInstanceOf(Error);
  });
});
