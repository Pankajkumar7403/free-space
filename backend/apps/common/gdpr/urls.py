from django.urls import path
from apps.common.gdpr import views

app_name = "gdpr"

urlpatterns = [
    path("export/",         views.GDPRDataExportView.as_view(),    name="data-export"),
    path("delete-account/", views.GDPRDeleteAccountView.as_view(), name="delete-account"),
]
