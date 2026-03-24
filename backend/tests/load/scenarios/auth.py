"""Shared auth mixin — all user types inherit this for login."""
from __future__ import annotations

import random
import string

from locust import HttpUser


class AuthScenario(HttpUser):
    abstract = True

    _token: str = ""
