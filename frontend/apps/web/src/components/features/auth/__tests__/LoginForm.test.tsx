// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/auth/__tests__/LoginForm.test.tsx
//
// Tests for the LoginForm component.
// Uses MSW to mock HTTP — no real network calls.

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { server } from '@/test/mswServer';
import { LoginForm } from '../LoginForm';

// ─── Render helpers ────────────────────────────────────────────────────────────
function renderLoginForm() {
  return render(<LoginForm />);
}

// ─── Tests ────────────────────────────────────────────────────────────────────
describe('LoginForm', () => {
  const user = userEvent.setup();

  describe('rendering', () => {
    it('renders email and password fields', () => {
      renderLoginForm();

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders link to register page', () => {
      renderLoginForm();
      expect(screen.getByRole('link', { name: /sign up/i })).toBeInTheDocument();
    });

    it('renders forgot password link', () => {
      renderLoginForm();
      expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument();
    });
  });

  describe('validation', () => {
    it('shows email validation error when email is invalid', async () => {
      renderLoginForm();

      await user.type(screen.getByLabelText(/email address/i), 'not-an-email');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
      });
    });

    it('shows password required error when password is empty', async () => {
      renderLoginForm();

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it('does not submit when fields are empty', async () => {
      const fetchSpy = vi.spyOn(global, 'fetch');
      renderLoginForm();

      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // No API calls should be made on validation failure
      expect(fetchSpy).not.toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.anything(),
      );
    });
  });

  describe('password visibility toggle', () => {
    it('toggles password visibility when eye button is clicked', async () => {
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');

      await user.click(screen.getByRole('button', { name: /show password/i }));
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(screen.getByRole('button', { name: /hide password/i }));
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('submission', () => {
    it('shows loading state while submitting', async () => {
      // Delay the response to see the loading state
      server.use(
        http.post('http://localhost:8000/api/v1/users/auth/login/', async () => {
          await new Promise((r) => setTimeout(r, 100));
          return HttpResponse.json({ user: {}, tokens: {} });
        }),
      );

      renderLoginForm();
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');

      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Button should be disabled and show loading text
      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
    });

    it('shows server error message on failed login', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/auth/login/', () =>
          HttpResponse.json(
            {
              error_code: 'AUTHENTICATION_FAILED',
              message:    'Invalid email or password.',
              details:    {},
            },
            { status: 401 },
          ),
        ),
      );

      renderLoginForm();
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/invalid email or password/i);
      });
    });

    it('maps field-level validation errors from server to form fields', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/auth/login/', () =>
          HttpResponse.json(
            {
              error_code: 'VALIDATION_ERROR',
              message:    'Validation failed.',
              details:    { email: ['Enter a valid email address.'] },
            },
            { status: 400 },
          ),
        ),
      );

      renderLoginForm();
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText(/enter a valid email address/i)).toBeInTheDocument();
      });
    });
  });
});
