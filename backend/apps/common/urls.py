from django.urls import path
from apps.common.views import HealthCheckView, ReportCreateView

app_name = "common"

urlpatterns = [
    path("", ReportCreateView.as_view(), name="report-create"),
]
