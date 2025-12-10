from django.urls import path
from .views import *

urlpatterns = [
    path("auth/login", AuthEmailView.as_view(), name="login"),
    path("items", LostItemCreateView.as_view(), name="lost-item-create"), #POST
    path("items/list", ItemsListView.as_view()), #GET
    path("items/cease/<int:request_id>", CeaseLostItemView.as_view(), name="item-cease"), #PATCH
]
