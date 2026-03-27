"""
Integration test: User Registration → Post Creation flow.

This tests that a freshly registered user can immediately create a post.
These tests are marked 'integration' and get django_db automatically
via conftest.py's pytest_collection_modifyitems hook.
"""

from rest_framework.test import APIClient


class TestUserPostFlow:
    """
    Smoke-test the critical path: register → authenticate → create post.
    """

    def test_new_user_can_create_post(self, db):
        # 1. Register
        client = APIClient()
        reg_response = client.post(
            "/api/users/register/",
            {
                "email": "newbie@example.com",
                "username": "newbie",
                "password": "strongpass123",
            },
        )
        assert reg_response.status_code == 201

        # 2. Authenticate (get token)
        login_response = client.post(
            "/api/auth/login/",
            {
                "email": "newbie@example.com",
                "password": "strongpass123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.data.get("access")
        assert token, "Expected JWT access token in login response"

        # 3. Create a post
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        post_response = client.post(
            "/api/posts/",
            {
                "content": "My first post!",
            },
        )
        assert post_response.status_code == 201
        assert post_response.data["content"] == "My first post!"
