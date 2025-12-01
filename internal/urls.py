from django.urls import path
from .views import EmailSendView, FoundItemSyncView

urlpatterns = [
    path("email/send", EmailSendView.as_view(), name="email_send"),
    path("found-items/sync", FoundItemSyncView.as_view(), name="found_items_sync"),
]
