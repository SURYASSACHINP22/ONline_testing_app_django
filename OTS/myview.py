from django.shortcuts import render
from django.http import HttpResponseRedirect
from OTS.models import Candidate, Question, Result, MembershipPlan
from OTS.decorators import candidate_login_required
from OTS import services
import random


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
    return render(request, 'registration.html', {'userStatus': user_status})


def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        candidate = services.authenticate_candidate(username, password)
        if candidate:
            request.session['username'] = candidate.username
            request.session['name'] = candidate.name
            return HttpResponseRedirect("home")
        return render(request, 'login.html', {'loginError': 'Invalid username or password'})
    return render(request, 'login.html')


@candidate_login_required
def candidateHome(request):
    candidate = Candidate.objects.filter(username=request.session['username']).select_related('membership_plan').first()
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
    candidate = Candidate.objects.filter(username=request.session['username']).select_related('membership_plan').first()
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
    services.calculate_and_save_result(request.session['username'], request.POST)
    return HttpResponseRedirect("result")


@candidate_login_required
def testResultHistory(request):
    candidate = Candidate.objects.get(username=request.session['username'])
    results = Result.objects.filter(username=candidate)
    return render(request, 'candidate_history.html', {'candidate': candidate, 'results': results})


@candidate_login_required
def showTestResult(request):
    results = Result.objects.filter(username__username=request.session['username']).order_by('-resultid')[:1]
    return render(request, 'show_result.html', {'results': results})


def logoutView(request):
    if 'name' in request.session and 'username' in request.session:
        del request.session['name']
        del request.session['username']
    return HttpResponseRedirect("login")


@candidate_login_required
def deleteAccountView(request):
    if request.method == 'POST':
        username = request.session.get('username')
        services.delete_candidate_account(username)
        for key in list(request.session.keys()):
            del request.session[key]
        request.session['flash_message'] = 'Your account and all data have been deleted.'
        return HttpResponseRedirect("/OTS/")
    return render(request, 'delete_account.html')


@candidate_login_required
def membershipPlansView(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id') or None
        if services.assign_membership_plan(request.session['username'], plan_id):
            request.session['flash_message'] = 'Membership plan updated.'
        return HttpResponseRedirect("membership")
    plans = MembershipPlan.objects.filter(is_active=True)
    candidate = Candidate.objects.filter(username=request.session['username']).select_related('membership_plan').first()
    current_plan = candidate.membership_plan if candidate else None
    flash = request.session.pop('flash_message', None)
    return render(request, 'membership_plans.html', {
        'plans': plans, 'current_plan': current_plan, 'flash_message': flash
    })
