from rest_framework import serializers


class GDPRExportRequestSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(
        help_text="Must be true to confirm the export request.",
    )

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm the export request.")
        return value


class GDPRDeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        help_text="Your current password for identity verification.",
    )
    confirm_phrase = serializers.CharField(
        help_text="Type exactly: DELETE MY ACCOUNT",
    )

    def validate_confirm_phrase(self, value):
        if value.strip() != "DELETE MY ACCOUNT":
            raise serializers.ValidationError(
                "Confirmation phrase must be exactly: DELETE MY ACCOUNT"
            )
        return value
