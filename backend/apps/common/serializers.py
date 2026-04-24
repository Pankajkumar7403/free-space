from rest_framework import serializers
from apps.common.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "reported_user", "reported_post", "reported_comment",
                  "reason", "details", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, data):
        targets = [data.get("reported_user"), data.get("reported_post"), data.get("reported_comment")]
        if len([t for t in targets if t is not None]) != 1:
            raise serializers.ValidationError(
                "Exactly one of reported_user, reported_post, reported_comment must be provided."
            )
        return data
