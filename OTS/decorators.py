"""
LLD: Decorator pattern – reusable login check for candidate-only views.
"""
from functools import wraps
from django.http import HttpResponseRedirect


def candidate_login_required(view_func):
    """Redirect to login if session has no 'name' or 'username'. Use on candidate-only views."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if 'name' not in request.session or 'username' not in request.session:
            return HttpResponseRedirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped
