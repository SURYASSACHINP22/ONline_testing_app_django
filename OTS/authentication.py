"""
Auth glue between Candidate model, Django, DRF, and JWT.

- CandidateBackend + CandidateUser: Django AUTHENTICATION_BACKENDS; password path calls
  services.authenticate_candidate (hashing / legacy upgrade — services.py).
- CandidateJWTAuthentication: DRF; reads JWT from Bearer header or HttpOnly access_token cookie
  (set in myview._set_auth_cookies). Produces request.user as CandidateUser for viewsets.
- get_candidate_username_from_request: shared decode for HTML @candidate_login_required.
"""
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
            # Wrap DB row as a minimal "user" for Django admin / JWT user_id claims.
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
    """
    Decode JWT from Authorization: Bearer <token> OR cookie access_token (HttpOnly from myview).

    Used by: OTS.decorators.candidate_login_required (HTML gate).
    Same lookup order as CandidateJWTAuthentication.authenticate (DRF API gate).
    """
    token = None
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
    if not token:
        token = request.COOKIES.get('access_token')
    return _decode_token_and_get_username(token)


class CandidateJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF entry point: sets request.user to CandidateUser when a valid access JWT is present.

    Token sources (same as get_candidate_username_from_request):
      1) Authorization: Bearer …  — typical for APIClient / SPA in memory
      2) Cookie access_token      — set by myview._set_auth_cookies after HTML login

    Validates signature via SIMPLE_JWT / SECRET_KEY, then loads Candidate by username from payload.
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
