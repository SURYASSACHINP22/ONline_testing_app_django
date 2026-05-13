"""
LLD: Decorator pattern – reusable login check for candidate-only views.

Uses OTS.authentication.get_candidate_username_from_request so HTML pages accept the same
HttpOnly access_token cookie set in myview._set_auth_cookies (layer 2), not only session auth.
"""
from functools import wraps
from django.http import HttpResponseRedirect
from .authentication import get_candidate_username_from_request
from .models import Candidate


def candidate_login_required(view_func):
    """
    Gate server-rendered views: no valid JWT → redirect to login.

    On success: loads Candidate from DB, sets request.candidate for myview handlers.
    """
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
