from django.contrib.auth import authenticate, login, logout
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .inference import predict
from .models import Prediction
from .serializers import PredictionSerializer, RegisterSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = authenticate(request, username=request.data.get("username", ""), password=request.data.get("password", ""))
        if user is None:
            return Response({"detail":"Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({"id":user.id,"username":user.username,"email":user.email})

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail":"Logged out."})

class MeView(APIView):
    def get(self, request):
        return Response({"id":request.user.id,"username":request.user.username,"email":request.user.email})

class PredictionListCreateView(generics.ListCreateAPIView):
    serializer_class = PredictionSerializer
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)
    def create(self, request, *args, **kwargs):
        image = request.FILES.get("image")
        if not image:
            return Response({"image":["Upload a leaf image."]}, status=status.HTTP_400_BAD_REQUEST)
        if image.size > 5 * 1024 * 1024:
            return Response({"image":["Image must be 5 MB or smaller."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            disease, confidence, demo_mode = predict(image)
        except Exception as exc:
            return Response({"detail":f"Could not process image: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        item = Prediction.objects.create(user=request.user, image=image, disease=disease, confidence=confidence, demo_mode=demo_mode)
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

class DashboardView(APIView):
    def get(self, request):
        queryset = Prediction.objects.filter(user=request.user)
        total = queryset.count()
        flagged = queryset.filter(disease__icontains="possible").count()
        recent = queryset[:5]
        return Response({"total_scans":total,"flagged_scans":flagged,"healthy_scans":total-flagged,"recent":PredictionSerializer(recent,many=True,context={"request":request}).data})
