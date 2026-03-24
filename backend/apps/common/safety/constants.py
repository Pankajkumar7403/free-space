"""
LGBTQ+ community safety constants.
Crisis resources, safe messaging thresholds, outing prevention config.
"""

# -- Crisis resources ---------------------------------------------------------
CRISIS_RESOURCES: dict[str, dict] = {
    "US": {
        "The Trevor Project": {
            "description": "Crisis intervention for LGBTQ+ youth",
            "phone": "1-866-488-7386",
            "text":  "Text START to 678-678",
            "chat":  "https://www.thetrevorproject.org/get-help/",
        },
        "Crisis Text Line": {
            "description": "24/7 text-based crisis support",
            "text": "Text HOME to 741741",
        },
        "988 Suicide & Crisis Lifeline": {
            "description": "National crisis support",
            "phone": "988",
            "chat":  "https://988lifeline.org/chat/",
        },
    },
    "UK": {
        "Switchboard LGBT+": {
            "description": "LGBT+ helpline",
            "phone": "0800 0119 100",
            "chat":  "https://switchboard.lgbt/",
        },
        "Samaritans": {
            "description": "Emotional support 24/7",
            "phone": "116 123",
        },
    },
    "IN": {
        "iCall": {
            "description": "Psychosocial helpline",
            "phone": "9152987821",
        },
        "Vandrevala Foundation": {
            "description": "Mental health helpline",
            "phone": "1860-2662-345",
        },
    },
    "DEFAULT": {
        "International Association for Suicide Prevention": {
            "description": "Find a crisis centre near you",
            "website": "https://www.iasp.info/resources/Crisis_Centres/",
        },
    },
}

# -- Safe messaging -----------------------------------------------------------
# Posts with these visibility levels auto-blur images from non-followers
SAFE_IMAGE_BLUR_VISIBILITIES = frozenset({"followers_only", "close_friends"})

# -- Outing prevention --------------------------------------------------------
# These fields on User are hidden to non-followers by default
PRIVATE_IDENTITY_FIELDS = frozenset({
    "pronouns", "gender_identity", "sexual_orientation",
})

# Audit log Redis key: who viewed a user's identity
IDENTITY_VIEW_AUDIT_KEY = "audit:identity_view:{viewer_id}:{profile_id}"
IDENTITY_VIEW_AUDIT_TTL = 7 * 24 * 3600   # 7 days
