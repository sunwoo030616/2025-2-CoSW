from django.urls import path
from .views import EmailSendView

urlpatterns = [
    # /internal/email/send
    path("email/send", EmailSendView.as_view(), name="email_send"),
]
