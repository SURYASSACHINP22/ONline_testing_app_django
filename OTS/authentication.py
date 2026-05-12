from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from rest_framework import authentication
from rest_framework import exceptions
from .models import Candidate
from . import services

class CandidateBackend(BaseBackend):
    """
    Custom authentication backend for Candidate model to work with JWT
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        candidate = services.authenticate_candidate(username, password)
        if candidate:
            # Create a mock user object that JWT can work with
            return CandidateUser(candidate)
        return None

    def get_user(self, user_id):
        try:
            candidate = Candidate.objects.get(pk=user_id)
            return CandidateUser(candidate)
        except Candidate.DoesNotExist:
            return None

class CandidateUser:
    """
    Mock user object that wraps Candidate for JWT compatibility
    """
    def __init__(self, candidate):
        self.candidate = candidate
        self.pk = candidate.username  # Use username as primary key
        self.username = candidate.username
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False

    def __str__(self):
        return self.username

    def __eq__(self, other):
        if isinstance(other, CandidateUser):
            return self.pk == other.pk
        return False

    def __hash__(self):
        return hash(self.pk)

    # Required attributes for Django auth
    @property
    def is_authenticated(self):
        return True

    def has_perm(self, perm, obj=None):
        return False

    def has_perms(self, perm_list, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False


def _decode_token_and_get_username(token):
    if not token:
        return None

    # Import lazily so standalone scripts can call django.setup() first.
    from rest_framework_simplejwt.backends import TokenBackend

    algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
    backend = TokenBackend(
        algorithm=algorithm,
        signing_key=settings.SECRET_KEY,
        verifying_key=settings.SIMPLE_JWT.get('VERIFYING_KEY', ''),
        audience=settings.SIMPLE_JWT.get('AUDIENCE'),
        issuer=settings.SIMPLE_JWT.get('ISSUER'),
        leeway=settings.SIMPLE_JWT.get('LEEWAY', 0),
    )
    try:
        payload = backend.decode(token, verify=True)
        return payload.get('user_id') or payload.get('username')
    except Exception:
        return None


def get_candidate_username_from_request(request):
    """Return a username from a valid JWT in the Authorization header or access_token cookie."""
    token = None
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
    if not token:
        token = request.COOKIES.get('access_token')
    return _decode_token_and_get_username(token)


class CandidateJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication for Candidate JWTs from Authorization header or access_token cookie.
    """

    def authenticate(self, request):
        token = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        if not token:
            token = request.COOKIES.get('access_token')
        if not token:
            return None

        username = _decode_token_and_get_username(token)
        if not username:
            raise exceptions.AuthenticationFailed('Invalid token')

        candidate = Candidate.objects.filter(username=username).first()
        if not candidate:
            raise exceptions.AuthenticationFailed('Candidate not found')

        return CandidateUser(candidate), token