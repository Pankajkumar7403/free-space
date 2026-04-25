// 📍 LOCATION: free-space/frontend/apps/mobile/app/(auth)/login.tsx
//
// Login screen — uses the same Zod schema and api-client as the web app.
// React Native implementation of the same form logic.

import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, ScrollView,
  ActivityIndicator, StyleSheet,
} from 'react-native';
import { Link, useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Eye, EyeOff } from 'lucide-react-native';

import { loginSchema, type LoginFormValues } from '@/lib/validators';
import { authApi } from '@qommunity/api-client';
import { ApiException } from '@qommunity/types';

import { useAuthStore } from '@/stores/authStore';
import { saveTokens } from '@/lib/session';

// ─── Design tokens (mirrors web CSS vars) ────────────────────────────────────
const COLORS = {
  primary:    '#7C3AED',
  background: '#0d0d14',
  surface:    '#16162a',
  border:     '#2a2a4a',
  text:       '#f1f0ff',
  muted:      '#7b7a9d',
  error:      '#f87171',
} as const;

export default function LoginScreen() {
  const router    = useRouter();
  const insets    = useSafeAreaInsets();
  const setAuth   = useAuthStore((s) => s.setAuth);

  const [showPassword, setShowPassword] = useState(false);
  const [serverError,  setServerError]  = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    try {
      const { user, tokens } = await authApi.login(values);
      await saveTokens(tokens.access, tokens.refresh);
      setAuth(user, tokens.access, tokens.refresh);
      router.replace('/(main)/feed');
    } catch (error) {
      if (error instanceof ApiException) {
        if (error.isValidationError()) {
          const fieldErrors = error.getFieldErrors();
          Object.entries(fieldErrors).forEach(([field, message]) => {
            setError(field as keyof LoginFormValues, { message });
          });
        } else {
          setServerError(error.message);
        }
      } else {
        setServerError('Something went wrong. Please try again.');
      }
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: COLORS.background }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar style="light" />
      <ScrollView
        contentContainerStyle={[
          styles.container,
          { paddingTop: insets.top + 32, paddingBottom: insets.bottom + 32 },
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Text style={styles.logoQ}>Q</Text>
          <Text style={styles.logoRest}>ommunity</Text>
        </View>
        <Text style={styles.tagline}>Your space. Your pride. 🏳️‍🌈</Text>

        {/* Form card */}
        <View style={styles.card}>
          <Text style={styles.heading}>Welcome back</Text>

          {/* Server error */}
          {serverError && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>{serverError}</Text>
            </View>
          )}

          {/* Email field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Email address</Text>
            <Controller
              control={control}
              name="email"
              render={({ field: { onChange, onBlur, value } }) => (
                <TextInput
                  style={[styles.input, errors.email && styles.inputError]}
                  placeholder="you@example.com"
                  placeholderTextColor={COLORS.muted}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  returnKeyType="next"
                  onBlur={onBlur}
                  onChangeText={onChange}
                  value={value}
                  accessibilityLabel="Email address"
                  accessibilityHint="Enter your Qommunity account email"
                />
              )}
            />
            {errors.email && (
              <Text style={styles.fieldError} accessibilityRole="alert">
                {errors.email.message}
              </Text>
            )}
          </View>

          {/* Password field */}
          <View style={styles.fieldGroup}>
            <View style={styles.labelRow}>
              <Text style={styles.label}>Password</Text>
              <Link href="/(auth)/forgot-password" style={styles.forgotLink}>
                Forgot password?
              </Link>
            </View>
            <Controller
              control={control}
              name="password"
              render={({ field: { onChange, onBlur, value } }) => (
                <View style={styles.passwordContainer}>
                  <TextInput
                    style={[styles.input, styles.passwordInput, errors.password && styles.inputError]}
                    placeholder="••••••••"
                    placeholderTextColor={COLORS.muted}
                    secureTextEntry={!showPassword}
                    autoComplete="current-password"
                    returnKeyType="done"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    onSubmitEditing={handleSubmit(onSubmit)}
                    value={value}
                    accessibilityLabel="Password"
                  />
                  <TouchableOpacity
                    style={styles.eyeButton}
                    onPress={() => setShowPassword((v) => !v)}
                    accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
                    accessibilityRole="button"
                  >
                    {showPassword
                      ? <EyeOff size={18} color={COLORS.muted} />
                      : <Eye     size={18} color={COLORS.muted} />
                    }
                  </TouchableOpacity>
                </View>
              )}
            />
            {errors.password && (
              <Text style={styles.fieldError} accessibilityRole="alert">
                {errors.password.message}
              </Text>
            )}
          </View>

          {/* Submit button */}
          <TouchableOpacity
            style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
            onPress={handleSubmit(onSubmit)}
            disabled={isSubmitting}
            accessibilityRole="button"
            accessibilityLabel="Sign in"
            accessibilityState={{ busy: isSubmitting }}
          >
            {isSubmitting
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={styles.submitButtonText}>Sign in</Text>
            }
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Don&apos;t have an account? </Text>
          <Link href="/(auth)/register" style={styles.footerLink}>
            Sign up
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    alignItems: 'center',
    gap: 0,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 6,
  },
  logoQ:    { fontSize: 40, fontFamily: 'Sora_700Bold',     color: COLORS.primary },
  logoRest: { fontSize: 40, fontFamily: 'Sora_700Bold',     color: COLORS.text },
  tagline:  { fontSize: 14, fontFamily: 'DMSans_400Regular', color: COLORS.muted, marginBottom: 32 },
  card: {
    width: '100%',
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 16,
  },
  heading: { fontSize: 22, fontFamily: 'Sora_600SemiBold', color: COLORS.text },
  errorBanner: {
    backgroundColor: 'rgba(248,113,113,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(248,113,113,0.3)',
    borderRadius: 10,
    padding: 12,
  },
  errorBannerText: { color: COLORS.error, fontSize: 13, fontFamily: 'DMSans_400Regular' },
  fieldGroup:  { gap: 6 },
  label:       { fontSize: 13, fontFamily: 'DMSans_500Medium', color: COLORS.text },
  labelRow:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  forgotLink:  { fontSize: 12, color: COLORS.muted, fontFamily: 'DMSans_400Regular' },
  input: {
    height: 48,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
    fontFamily: 'DMSans_400Regular',
    color: COLORS.text,
  },
  inputError:       { borderColor: COLORS.error },
  passwordContainer:{ position: 'relative' },
  passwordInput:    { paddingRight: 44 },
  eyeButton: {
    position: 'absolute',
    right: 14,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
  },
  fieldError: { fontSize: 12, color: COLORS.error, fontFamily: 'DMSans_400Regular' },
  submitButton: {
    height: 52,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  submitButtonDisabled: { opacity: 0.6 },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontFamily: 'Sora_600SemiBold',
    letterSpacing: 0.3,
  },
  footer:     { flexDirection: 'row', alignItems: 'center', marginTop: 24 },
  footerText: { fontSize: 14, color: COLORS.muted, fontFamily: 'DMSans_400Regular' },
  footerLink: { fontSize: 14, color: COLORS.primary, fontFamily: 'DMSans_500Medium' },
});
