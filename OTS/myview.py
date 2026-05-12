from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from OTS.models import Candidate, Question, Result, MembershipPlan
from OTS.decorators import candidate_login_required
from OTS import services
import random


def _set_auth_cookies(response, refresh):
    response.set_cookie(
        'access_token',
        str(refresh.access_token),
        httponly=True,
        samesite='Lax',
        secure=settings.JWT_COOKIE_SECURE,
    )
    response.set_cookie(
        'refresh_token',
        str(refresh),
        httponly=True,
        samesite='Lax',
        secure=settings.JWT_COOKIE_SECURE,
    )


def welcome(request):
    message = request.session.pop('flash_message', None)
    context = {'message': message} if message else {}
    return render(request, 'welcome.html', context)


def candidateRegistrationForm(request):
    plans = MembershipPlan.objects.filter(is_active=True)
    return render(request, 'registration_Form.html', {'plans': plans})


def candidateRegistration(request):
    if request.method != 'POST':
        return render(request, 'registration.html', {'userStatus': 3})
    username = request.POST.get('username')
    if not username:
        return render(request, 'registration.html', {'userStatus': 3})
    success, user_status = services.register_candidate(
        username=username,
        password=request.POST.get('password', ''),
        name=request.POST.get('name', ''),
        plan_id=request.POST.get('membership_plan') or None,
    )
    if success:
        candidate = Candidate.objects.filter(username=username).first()
        refresh = RefreshToken.for_user(candidate)
        response = HttpResponseRedirect('home')
        _set_auth_cookies(response, refresh)
        return response
    return render(request, 'registration.html', {'userStatus': user_status})


def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        candidate = services.authenticate_candidate(username, password)
        if candidate:
            refresh = RefreshToken.for_user(candidate)
            response = HttpResponseRedirect('home')
            _set_auth_cookies(response, refresh)
            return response
        return render(request, 'login.html', {'loginError': 'Invalid username or password'})
    return render(request, 'login.html')


@candidate_login_required
def candidateHome(request):
    candidate = request.candidate
    allowed = services.get_allowed_question_counts(candidate)
    flash = request.session.pop('flash_message', None)
    return render(request, 'home.html', {'allowed_question_counts': allowed, 'flash_message': flash})


@candidate_login_required
def testPaper(request):
    n_raw = request.GET.get('n')
    if n_raw is None:
        return HttpResponseRedirect("home")
    try:
        n = int(n_raw)
    except (ValueError, TypeError):
        return HttpResponseRedirect("home")
    candidate = request.candidate
    allowed = services.get_allowed_question_counts(candidate)
    if n not in allowed:
        request.session['flash_message'] = (
            'Your membership plan does not allow this test type. '
            'Allowed: %s question(s). Change plan in Membership plans.' % (', '.join(map(str, allowed)) or 'none')
        )
        return HttpResponseRedirect("home")
    question_pool = list(Question.objects.all())
    random.shuffle(question_pool)
    questions_list = question_pool[:n]
    return render(request, 'test_paper.html', {'questions': questions_list})


@candidate_login_required
def calculateTestResult(request):
    services.calculate_and_save_result(request.candidate.username, request.POST)
    return HttpResponseRedirect("result")


@candidate_login_required
def testResultHistory(request):
    candidate = request.candidate
    results = Result.objects.filter(username=candidate)
    return render(request, 'candidate_history.html', {'candidate': candidate, 'results': results})


@candidate_login_required
def showTestResult(request):
    results = Result.objects.filter(username__username=request.candidate.username).order_by('-resultid')[:1]
    return render(request, 'show_result.html', {'results': results})


def logoutView(request):
    response = HttpResponseRedirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@candidate_login_required
def deleteAccountView(request):
    if request.method == 'POST':
        username = request.candidate.username
        services.delete_candidate_account(username)
        request.session['flash_message'] = 'Your account and all data have been deleted.'
        response = HttpResponseRedirect('/OTS/')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
    return render(request, 'delete_account.html')


@candidate_login_required
def membershipPlansView(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id') or None
        if services.assign_membership_plan(request.candidate.username, plan_id):
            request.session['flash_message'] = 'Membership plan updated.'
        return HttpResponseRedirect('membership')
    plans = MembershipPlan.objects.filter(is_active=True)
    candidate = request.candidate
    current_plan = candidate.membership_plan if candidate else None
    flash = request.session.pop('flash_message', None)
    return render(request, 'membership_plans.html', {
        'plans': plans, 'current_plan': current_plan, 'flash_message': flash
    })
