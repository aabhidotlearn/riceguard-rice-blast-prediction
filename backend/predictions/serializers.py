from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Prediction

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class PredictionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Prediction
        fields = ("id", "image", "image_url", "disease", "confidence", "demo_mode", "created_at")
        read_only_fields = ("id", "disease", "confidence", "demo_mode", "created_at")
    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url
