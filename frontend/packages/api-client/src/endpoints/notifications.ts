// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/notifications.ts
//
// Notifications API calls
// Base URL: /api/v1/notifications/

import type { Notification, PaginatedResponse } from '@qommunity/types';
import { apiClient } from '../instance';

const BASE = '/notifications';

export const notificationsApi = {
  /**
   * GET /api/v1/notifications/
   */
  getNotifications: async (cursor?: string): Promise<PaginatedResponse<Notification>> => {
    const { data } = await apiClient.get<PaginatedResponse<Notification>>(`${BASE}/`, {
      params: { cursor },
    });
    return data;
  },

  /**
   * GET /api/v1/notifications/unread-count/
   * Lightweight endpoint polled by the notification bell.
   */
  getUnreadCount: async (): Promise<{ count: number }> => {
    const { data } = await apiClient.get<{ count: number }>(`${BASE}/unread-count/`);
    return data;
  },

  /**
   * POST /api/v1/notifications/{id}/read/
   */
  markRead: async (notificationId: string): Promise<void> => {
    await apiClient.post(`${BASE}/${notificationId}/read/`);
  },

  /**
   * POST /api/v1/notifications/read-all/
   */
  markAllRead: async (): Promise<void> => {
    await apiClient.post(`${BASE}/read-all/`);
  },

  /**
   * DELETE /api/v1/notifications/{id}/
   */
  deleteNotification: async (notificationId: string): Promise<void> => {
    await apiClient.delete(`${BASE}/${notificationId}/`);
  },

  /**
   * PATCH /api/v1/notifications/preferences/
   * Update per-type notification preferences.
   */
  updatePreferences: async (
    preferences: Record<string, boolean>,
  ): Promise<Record<string, boolean>> => {
    const { data } = await apiClient.patch<Record<string, boolean>>(
      `${BASE}/preferences/`,
      preferences,
    );
    return data;
  },

  /**
   * POST /api/v1/notifications/device-token/
   * Register FCM/APNs device token for push notifications (mobile only).
   */
  registerDeviceToken: async (payload: {
    token: string;
    platform: 'ios' | 'android';
  }): Promise<void> => {
    await apiClient.post(`${BASE}/device-token/`, payload);
  },
};
