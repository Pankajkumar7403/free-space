# Stage 2 Slice A: Event Contract Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify backend Kafka event payload contracts for likes/comments/follows so feed and notification consumers receive compatible data and user-facing side effects work reliably.

**Architecture:** Keep existing topics and producer/consumer structure, but define one canonical payload shape per topic and align producers + consumers to that shape. Add focused contract tests at service and consumer boundaries to prevent silent drift.

**Tech Stack:** Django 6, DRF, pytest, Kafka abstraction (`core.kafka`), notifications/feed apps.

---

## Scope Check

Stage 2 audit identified two independent subsystems:
1) Backend event contract drift (this plan)
2) Frontend route dead-end closure (`/p/[postId]`, etc.) (separate follow-up plan)

This plan intentionally covers only backend contract unification.

---

## File Structure

- Create: `backend/apps/notifications/tests/test_event_contracts.py`
- Modify: `backend/apps/notifications/events.py`
- Modify: `backend/apps/users/events.py`
- Modify: `backend/apps/users/services.py`
- Modify: `backend/apps/users/tests/test_services.py`
- Modify: `backend/apps/comments/events.py`
- Modify: `backend/apps/comments/services.py` (only if needed for parent-comment metadata)
- Modify: `backend/apps/comments/tests/test_services.py` (only if event payload assertions are added here)

---

### Task 1: Lock canonical consumer contract with failing tests

**Files:**
- Create: `backend/apps/notifications/tests/test_event_contracts.py`
- Test: `backend/apps/notifications/tests/test_event_contracts.py`

- [ ] **Step 1: Write failing consumer contract tests for like/comment/follow topics**

```python
import uuid
from unittest.mock import patch

import pytest

from apps.notifications.constants import NotificationType
from apps.notifications.events import handle_kafka_event


@pytest.mark.django_db
def test_like_created_contract_from_likes_producer_shape():
    payload = {
        "like_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "object_id": str(uuid.uuid4()),
        "object_type": "post",
        "author_id": str(uuid.uuid4()),
    }

    with patch("apps.notifications.events.create_notification") as mock_create:
        handle_kafka_event("like.created", payload)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        assert kwargs["notification_type"] == str(NotificationType.LIKE_POST)


@pytest.mark.django_db
def test_comment_created_contract_from_comments_producer_shape():
    payload = {
        "comment_id": str(uuid.uuid4()),
        "post_id": str(uuid.uuid4()),
        "author_id": str(uuid.uuid4()),
        "post_author_id": str(uuid.uuid4()),
    }

    with patch("apps.notifications.events.create_notification") as mock_create:
        handle_kafka_event("comment.created", payload)
        assert mock_create.call_count == 1


@pytest.mark.django_db
def test_user_followed_contract_from_users_producer_shape():
    payload = {"follower_id": str(uuid.uuid4()), "following_id": str(uuid.uuid4())}

    with patch("apps.notifications.events.create_notification") as mock_create:
        handle_kafka_event("user.followed", payload)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        assert kwargs["notification_type"] == str(NotificationType.FOLLOW)
```

- [ ] **Step 2: Run test to verify red state**

Run: `cd backend && uv run pytest apps/notifications/tests/test_event_contracts.py -v`

Expected: FAIL on current `like.created` and `comment.created` field expectations.

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/apps/notifications/tests/test_event_contracts.py
git commit -m "test(notifications): add failing kafka event contract tests"
```

---

### Task 2: Align notification consumer to producer payloads

**Files:**
- Modify: `backend/apps/notifications/events.py`
- Test: `backend/apps/notifications/tests/test_event_contracts.py`

- [ ] **Step 1: Update handler field mapping to canonical payloads**

```python
# like.created
liker_id = data.get("user_id")
target_author_id = data.get("author_id")
target_object_id = data.get("object_id")
object_type = data.get("object_type")

# comment.created
commenter_id = data.get("author_id")
post_author_id = data.get("post_author_id")
comment_id = data.get("comment_id")
```

- [ ] **Step 2: Keep topic names unchanged, only normalize payload interpretation**

```python
_HANDLERS = {
    "like.created": _handle_like_created,
    "comment.created": _handle_comment_created,
    "user.followed": _handle_user_followed,
}
```

- [ ] **Step 3: Run contract tests to green**

Run: `cd backend && uv run pytest apps/notifications/tests/test_event_contracts.py -v`

Expected: PASS.

- [ ] **Step 4: Commit consumer alignment**

```bash
git add backend/apps/notifications/events.py backend/apps/notifications/tests/test_event_contracts.py
git commit -m "fix(notifications): align kafka handlers with producer payload schema"
```

---

### Task 3: Implement `user.followed` producer and service wiring

**Files:**
- Modify: `backend/apps/users/events.py`
- Modify: `backend/apps/users/services.py`
- Modify: `backend/apps/users/tests/test_services.py`

- [ ] **Step 1: Add user follow event producer**

```python
# backend/apps/users/events.py
from dataclasses import dataclass
from core.kafka.base_event import BaseEvent
from core.kafka.producer import get_producer
from core.kafka.topics import Topics


@dataclass
class UserFollowedEvent(BaseEvent):
    event_type: str = Topics.USER_FOLLOWED
    follower_id: str = ""
    following_id: str = ""

    def to_key(self) -> str:
        return self.following_id


def emit_user_followed(*, follower_id: str, following_id: str) -> None:
    get_producer().send(
        Topics.USER_FOLLOWED,
        UserFollowedEvent(follower_id=follower_id, following_id=following_id),
    )
```

- [ ] **Step 2: Emit event when follow becomes accepted**

```python
# backend/apps/users/services.py
from apps.users.events import emit_user_followed

if status == FollowStatusChoices.ACCEPTED:
    emit_user_followed(follower_id=str(follower.pk), following_id=str(following.pk))
```

- [ ] **Step 3: Add failing-to-passing service tests**

```python
@patch("apps.users.services.emit_user_followed")
def test_follow_public_user_emits_user_followed(mock_emit, db):
    a = UserFactory(public=True)
    b = UserFactory(public=True)
    follow_user(follower_id=a.pk, following_id=b.pk)
    mock_emit.assert_called_once_with(follower_id=str(a.pk), following_id=str(b.pk))


@patch("apps.users.services.emit_user_followed")
def test_follow_private_user_does_not_emit_user_followed(mock_emit, db):
    a = UserFactory(public=True)
    b = UserFactory(private=True)
    follow_user(follower_id=a.pk, following_id=b.pk)
    mock_emit.assert_not_called()
```

- [ ] **Step 4: Run users service tests**

Run: `cd backend && uv run pytest apps/users/tests/test_services.py -v`

Expected: PASS with new follow-event assertions.

- [ ] **Step 5: Commit producer wiring**

```bash
git add backend/apps/users/events.py backend/apps/users/services.py backend/apps/users/tests/test_services.py
git commit -m "feat(users): emit user.followed event for accepted follows"
```

---

### Task 4: Ensure comment payload consistency for reply metadata

**Files:**
- Modify: `backend/apps/comments/events.py`
- Modify: `backend/apps/comments/tests/test_services.py` (or add a dedicated events test file)
- Optionally modify: `backend/apps/comments/services.py` only if event call needs additional context

- [ ] **Step 1: Extend `comment.created` event to include reply metadata when present**

```python
# backend/apps/comments/events.py (concept)
parent_comment_id = str(comment.parent_id) if comment.parent_id else ""
parent_comment_author_id = (
    str(comment.parent.author_id) if comment.parent_id else ""
)
```

- [ ] **Step 2: Add tests asserting emitted payload keys for top-level vs reply comment**

```python
@patch("apps.comments.events.get_producer")
def test_emit_comment_created_reply_payload_includes_parent_fields(...):
    ...
```

- [ ] **Step 3: Run comments tests**

Run: `cd backend && uv run pytest apps/comments/tests/test_services.py -v`

Expected: PASS with new payload assertions.

- [ ] **Step 4: Commit comment payload normalization**

```bash
git add backend/apps/comments/events.py backend/apps/comments/tests/test_services.py
git commit -m "fix(comments): normalize comment.created payload for replies"
```

---

### Task 5: End-to-end contract verification sweep

**Files:**
- Test: `backend/apps/notifications/tests/test_event_contracts.py`
- Test: `backend/apps/users/tests/test_services.py`
- Test: `backend/apps/comments/tests/test_services.py`
- Test: `backend/apps/likes/tests/test_services.py`

- [ ] **Step 1: Run focused slice test suite**

Run:
`cd backend && uv run pytest apps/notifications/tests/test_event_contracts.py apps/users/tests/test_services.py apps/comments/tests/test_services.py apps/likes/tests/test_services.py -v`

Expected: PASS.

- [ ] **Step 2: Run a quick integration sanity for notifications app**

Run:
`cd backend && uv run pytest apps/notifications/tests/test_services.py apps/notifications/tests/test_mutations.py -v`

Expected: PASS (or document any existing unrelated failures).

- [ ] **Step 3: Final slice commit**

```bash
git add -A
git commit -m "fix(stage2): unify kafka event contracts for likes comments and follows"
```

---

## Plan Self-Review

### Spec coverage
- Covers the top backend Stage 2 gap: producer/consumer contract drift and missing `user.followed` emission.
- Includes tests first and explicit verification gates.

### Placeholder scan
- No TBD/TODO placeholders.
- Each task includes concrete files, commands, and expected outcomes.

### Type/signature consistency
- Canonical payload field names are intentionally unified across producer->consumer paths.
- Topic names remain unchanged to avoid unnecessary migration scope.
