"""
LLD: Decorator pattern – reusable login check for candidate-only views.
"""
from functools import wraps
from django.http import HttpResponseRedirect
from .authentication import get_candidate_username_from_request
from .models import Candidate


def candidate_login_required(view_func):
    """Redirect to login if no valid JWT access token is present."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        username = get_candidate_username_from_request(request)
        if not username:
            return HttpResponseRedirect("login")
        candidate = Candidate.objects.filter(username=username).first()
        if not candidate:
            return HttpResponseRedirect("login")
        request.candidate = candidate
        return view_func(request, *args, **kwargs)
    return _wrapped
