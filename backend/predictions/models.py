from django.conf import settings
from django.db import models

class Prediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions")
    image = models.ImageField(upload_to="leaf_images/%Y/%m/")
    disease = models.CharField(max_length=80)
    confidence = models.FloatField()
    demo_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.disease} ({self.confidence:.0%}) — {self.user}"
