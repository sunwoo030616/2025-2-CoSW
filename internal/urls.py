from django.urls import path
from .views import*
urlpatterns = [
    path("email/send", EmailSendView.as_view(), name="email_send"),
    path("found-items/sync", FoundItemSyncView.as_view(), name="found_items_sync"),
    path("matching/daily", DailyMatchingView.as_view(), name="matching_daily"),
]
