from django.db import models
from pgvector.django import VectorField


# -------------------------
# USERS
# -------------------------
class Users(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


# -------------------------
# USER_LOST_ITEM
# -------------------------
class UserLostItem(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column="user_id")

    description = models.TextField(null=True, blank=True)
    original_image_url = models.CharField(max_length=500, null=True, blank=True)

    # pgvector 0.4.1 → dim / size 지원 안 함
    vlm_embedding = VectorField(null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_lost_item"

    def __str__(self):
        return f"{self.request_id} - {self.description}"


# -------------------------
# POLICE_FOUND_ITEM
# -------------------------
class PoliceFoundItem(models.Model):
    atc_id = models.CharField(max_length=50)
    fd_sn = models.CharField(max_length=10)

    item_name = models.CharField(max_length=200, null=True)
    category = models.CharField(max_length=100, null=True)
    found_location = models.CharField(max_length=200, null=True)
    found_date = models.DateField(null=True)

    item_desc = models.TextField(null=True)
    ai_generated_desc = models.TextField(null=True)

    police_image_url = models.CharField(max_length=500, null=True)
    raw_data = models.JSONField(default=dict, blank=True)

    # 역시 파라미터 없이
    vlm_embedding = VectorField(null=True)

    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "police_found_item"
        unique_together = (("atc_id", "fd_sn"),)

    def __str__(self):
        return f"{self.atc_id}-{self.fd_sn}"


# -------------------------
# NOTIFICATION_LOG
# -------------------------
class NotificationLog(models.Model):
    noti_id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column="user_id")
    request = models.ForeignKey(
        UserLostItem, on_delete=models.CASCADE, db_column="request_id"
    )

    atc_id = models.CharField(max_length=50)
    fd_sn = models.CharField(max_length=10)
    similarity_score = models.FloatField(null=True)

    rank = models.IntegerField(null=True)

    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_log"

    def __str__(self):
        return f"Noti {self.noti_id} to User {self.user_id}"
