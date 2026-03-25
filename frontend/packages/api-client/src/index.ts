// 📍 LOCATION: free-space/frontend/packages/api-client/src/index.ts
//
// Single import point: import { authApi, usersApi, ... } from '@qommunity/api-client'

export { apiClient, configureApiClient } from './instance';
export type { TokenStore } from './instance';

export { authApi }         from './endpoints/auth';
export { usersApi }        from './endpoints/users';
export { postsApi }        from './endpoints/posts';
export { feedApi }         from './endpoints/feed';
export { commentsApi }     from './endpoints/comments';
export { notificationsApi } from './endpoints/notifications';
