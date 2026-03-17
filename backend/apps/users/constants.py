# 📁 Location: backend/apps/users/constants.py

from django.db import models


class PronounChoices(models.TextChoices):
    HE_HIM       = "he/him",       "He/Him"
    SHE_HER      = "she/her",      "She/Her"
    THEY_THEM    = "they/them",    "They/Them"
    HE_THEY      = "he/they",      "He/They"
    SHE_THEY     = "she/they",     "She/They"
    ANY          = "any",          "Any pronouns"
    ASK_ME       = "ask me",       "Ask me"
    PREFER_NOT   = "prefer_not",   "Prefer not to say"
    CUSTOM       = "custom",       "Custom"


class GenderIdentityChoices(models.TextChoices):
    MAN                  = "man",                  "Man"
    WOMAN                = "woman",                "Woman"
    NON_BINARY           = "non_binary",           "Non-binary"
    GENDERQUEER          = "genderqueer",          "Genderqueer"
    GENDERFLUID          = "genderfluid",          "Genderfluid"
    AGENDER              = "agender",              "Agender"
    BIGENDER             = "bigender",             "Bigender"
    TRANSGENDER          = "transgender",          "Transgender"
    TWO_SPIRIT           = "two_spirit",           "Two-Spirit"
    QUESTIONING          = "questioning",          "Questioning"
    PREFER_NOT_TO_SAY    = "prefer_not",           "Prefer not to say"
    CUSTOM               = "custom",               "Custom (see bio)"


class SexualOrientationChoices(models.TextChoices):
    GAY                  = "gay",                  "Gay"
    LESBIAN              = "lesbian",              "Lesbian"
    BISEXUAL             = "bisexual",             "Bisexual"
    PANSEXUAL            = "pansexual",            "Pansexual"
    QUEER                = "queer",                "Queer"
    ASEXUAL              = "asexual",              "Asexual"
    AROMANTIC            = "aromantic",            "Aromantic"
    DEMISEXUAL           = "demisexual",           "Demisexual"
    STRAIGHT             = "straight",             "Straight/Heterosexual"
    QUESTIONING          = "questioning",          "Questioning"
    PREFER_NOT_TO_SAY    = "prefer_not",           "Prefer not to say"
    CUSTOM               = "custom",               "Custom (see bio)"


class AccountPrivacyChoices(models.TextChoices):
    PUBLIC          = "public",          "Public"
    FOLLOWERS_ONLY  = "followers_only",  "Followers only"
    PRIVATE         = "private",         "Private"


class VisibilityChoices(models.TextChoices):
    """Controls who can see a specific identity field."""
    PUBLIC        = "public",         "Everyone"
    FOLLOWERS     = "followers",      "Followers only"
    ONLY_ME       = "only_me",        "Only me"


class FollowStatusChoices(models.TextChoices):
    PENDING   = "pending",   "Pending"
    ACCEPTED  = "accepted",  "Accepted"
    REJECTED  = "rejected",  "Rejected"