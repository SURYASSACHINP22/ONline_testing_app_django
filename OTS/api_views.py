"""
REST API viewsets mounted under /OTS/api/ (see OTS.urls DefaultRouter).

Security-related flows in this module:
  • CandidateViewSet.login / register → services.authenticate_candidate / register_candidate
    (password hashing — services.py), then RefreshToken.for_user → JSON body includes tokens
    (SPA/mobile); browser HTML flow uses cookies from myview._set_auth_cookies instead.
  • CandidateViewSet.partial_update → self-service only {name}; rejects points etc. (layer 4).
  • QuestionViewSet → QuestionSerializer vs QuestionAdminSerializer by admin flag (layer 3).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Candidate, Question, Result, MembershipPlan
from .serializers import (
    CandidateSerializer,
    CandidateAdminSerializer,
    CandidateSelfUpdateSerializer,
    QuestionSerializer,
    QuestionAdminSerializer,
    ResultSerializer,
    MembershipPlanSerializer,
    MembershipPlanAdminSerializer,
)
from .permissions import IsAdminUserCustom, IsAdminOrReadOnly, is_admin_user
from . import services

class CandidateViewSet(viewsets.ModelViewSet):
    """
    /OTS/api/candidates/

    Auth: DRF resolves request.user via settings.REST_FRAMEWORK DEFAULT_AUTHENTICATION_CLASSES
    (Session → CandidateJWTAuthentication → JWTAuthentication). CandidateJWT reads Bearer header
    or HttpOnly access_token cookie (same token shape from login).

    Self-service PATCH: partial_update below restricts body keys to {'name'} only so clients
    cannot inflate points or test_attempted even if they bypass serializer fields.
    """
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'put', 'delete', 'head', 'options', 'post']
    lookup_field = 'username'

    def get_permissions(self):
        if self.action in ['login', 'register']:
            return [AllowAny()]
        if self.action == 'list':
            return [IsAdminUserCustom()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if is_admin_user(self.request.user):
            return CandidateAdminSerializer
        if self.action in ['partial_update', 'update']:
            return CandidateSelfUpdateSerializer
        return CandidateSerializer

    def get_queryset(self):
        if is_admin_user(self.request.user):
            username = self.request.query_params.get('username')
            if username:
                return Candidate.objects.filter(username=username)
            return Candidate.objects.all()
        username = getattr(self.request.user, 'username', None)
        return Candidate.objects.filter(username=username)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """GET /OTS/api/candidates/profile/ or /OTS/api/candidates/profile/?username=<username>"""
        if is_admin_user(request.user):
            username = request.query_params.get('username')
            if not username:
                return Response({'error': 'Please provide username for admin profile lookup.'}, status=status.HTTP_400_BAD_REQUEST)
            candidate = Candidate.objects.filter(username=username).first()
            if not candidate:
                return Response({'error': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
            return Response(CandidateAdminSerializer(candidate).data)

        candidate = Candidate.objects.filter(username=getattr(request.user, 'username', None)).first()
        if not candidate:
            return Response({'error': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CandidateSerializer(candidate).data)

    def update(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Use PATCH for updating profile name only.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return Response({'error': 'Use register endpoint to create candidate.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can delete candidates.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /OTS/api/candidates/<username>/

        Non-admin: defense in depth (layer 4):
          1. Only the logged-in candidate's own row (username match).
          2. Reject if JSON keys are not a subset of {'name'} — blocks {'points': 999} etc.
          3. CandidateSelfUpdateSerializer then only allows 'name' field through to the model.

        Admin: delegates to ModelViewSet.partial_update (CandidateAdminSerializer).
        """
        if not is_admin_user(request.user):
            obj = self.get_object()
            if obj.username != getattr(request.user, 'username', None):
                return Response({'error': 'You can edit only your own profile.'}, status=status.HTTP_403_FORBIDDEN)
            allowed_fields = {'name'}
            incoming_fields = set(request.data.keys())
            if not incoming_fields.issubset(allowed_fields):
                return Response(
                    {'error': 'You can update only name field.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(CandidateSerializer(obj).data)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        POST .../candidates/login/ — body: username, password.
        services.authenticate_candidate (hash + legacy upgrade) → RefreshToken.for_user(candidate).
        Response includes access/refresh in JSON (API clients); not the same as myview cookies.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        candidate = services.authenticate_candidate(username, password)
        if candidate:
            refresh = RefreshToken.for_user(candidate)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'candidate': CandidateSerializer(candidate).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """POST .../candidates/register/ — services.register_candidate (hashed password) → JWT in response."""
        success, message = services.register_candidate(
            username=request.data.get('username'),
            password=request.data.get('password'),
            name=request.data.get('name'),
            plan_id=request.data.get('membership_plan')
        )
        if success:
            candidate = Candidate.objects.filter(username=request.data.get('username')).first()
            refresh = RefreshToken.for_user(candidate)
            return Response({
                'message': 'Registration successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'candidate': CandidateSerializer(candidate).data,
            })
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    def get_throttles(self):
        if self.action in ['login', 'register']:
            throttle = ScopedRateThrottle()
            throttle.scope = self.action
            return [throttle]
        return super().get_throttles()

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Question.objects.all()
        qid = self.request.query_params.get('qid')
        if qid:
            queryset = queryset.filter(qid=qid)
        return queryset

    def get_serializer_class(self):
        # Admin/staff → QuestionAdminSerializer (includes ans). Candidate → QuestionSerializer (no ans).
        if is_admin_user(self.request.user):
            return QuestionAdminSerializer
        return QuestionSerializer

    def create(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can create questions.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can update questions.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can update questions.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can delete questions.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        resultid = self.request.query_params.get('resultid')
        username = self.request.query_params.get('username')

        if is_admin_user(self.request.user):
            queryset = Result.objects.all()
            if resultid:
                queryset = queryset.filter(resultid=resultid)
            if username:
                queryset = queryset.filter(username__username=username)
            return queryset

        queryset = Result.objects.filter(username__username=self.request.user.username)
        if resultid:
            queryset = queryset.filter(resultid=resultid)
        return queryset

    def create(self, request, *args, **kwargs):
        return Response({'error': 'Use submit_test endpoint to create results.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['post'])
    def submit_test(self, request):
        services.calculate_and_save_result(request.user.username, request.data)
        return Response({'message': 'Test submitted successfully'})

class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.filter(is_active=True)
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if is_admin_user(self.request.user):
            return MembershipPlan.objects.all()
        return MembershipPlan.objects.filter(is_active=True)

    def get_serializer_class(self):
        if is_admin_user(self.request.user):
            return MembershipPlanAdminSerializer
        return MembershipPlanSerializer

    def create(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can create membership plans.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can update membership plans.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can update membership plans.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin can delete membership plans.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

# Custom token views for better error handling
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token'

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                # Add candidate data to response
                username = request.data.get('username')
                candidate = Candidate.objects.filter(username=username).first()
                if candidate:
                    response.data['candidate'] = CandidateSerializer(candidate).data
            return response
        except Exception as e:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)