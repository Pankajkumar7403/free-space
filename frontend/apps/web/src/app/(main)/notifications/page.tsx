// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/notifications/page.tsx

'use client';

import { useCallback, useEffect, useState } from 'react';
import type { Notification } from '@qommunity/types';
import { apiClient } from '@qommunity/api-client';

const POLL_INTERVAL_MS = 30_000;

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const { data } = await apiClient.get<{ results: Notification[] }>('/notifications/');
      setNotifications(data.results);
      setError(null);
    } catch {
      setError('Failed to load notifications.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markRead = useCallback(async (id: string) => {
    try {
      await apiClient.patch(`/notifications/${id}/`, { is_read: true });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      // non-critical
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchNotifications]);

  if (isLoading) {
    return (
      <div className="p-4">
        <p className="text-muted-foreground">Loading notifications...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="p-4">
        <p className="text-muted-foreground">No notifications yet.</p>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto p-4 space-y-2">
      <h1 className="text-xl font-semibold mb-4">Notifications</h1>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`p-3 rounded-lg border cursor-pointer transition-colors ${
            notification.is_read
              ? 'bg-background border-border'
              : 'bg-muted border-primary/20'
          }`}
          onClick={() => !notification.is_read && markRead(notification.id)}
        >
          <p className="text-sm">
            <span className="font-medium">{notification.actor.username}</span>{' '}
            {verbToText(notification.verb)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(notification.created_at).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}

function verbToText(verb: Notification['verb']): string {
  const map: Record<Notification['verb'], string> = {
    liked_post: 'liked your post',
    liked_comment: 'liked your comment',
    commented_on_post: 'commented on your post',
    replied_to_comment: 'replied to your comment',
    followed_you: 'followed you',
    follow_request: 'sent you a follow request',
    follow_request_accepted: 'accepted your follow request',
    mentioned_in_post: 'mentioned you in a post',
    mentioned_in_comment: 'mentioned you in a comment',
    post_approved: 'approved your post',
  };
  return map[verb] ?? verb;
}
