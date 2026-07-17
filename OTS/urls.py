from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from OTS.myview import (
    welcome,
    candidateRegistrationForm,
    candidateRegistration,
    loginView,
    candidateHome,
    testPaper,
    calculateTestResult,
    testResultHistory,
    showTestResult,
    logoutView,
    deleteAccountView,
    membershipPlansView,
)
from OTS.api_views import (
    CandidateViewSet,
    QuestionViewSet,
    ResultViewSet,
    MembershipPlanViewSet,
    CustomTokenObtainPairView,
)

app_name = 'OTS'

# API Router
router = DefaultRouter()
router.register(r'candidates', CandidateViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'results', ResultViewSet)
router.register(r'membership-plans', MembershipPlanViewSet)

urlpatterns = [
    path('home/api/', RedirectView.as_view(url='/OTS/api/', permanent=False)),
    path('api/', include(router.urls)),
    # JWT Token endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', welcome, name='welcome'),
    path('new-candidate', candidateRegistrationForm, name='registrationForm'),
    path('store-candidate', candidateRegistration, name='storeCandidate'),
    path('login', loginView, name='login'),
    path('home', candidateHome, name='home'),
    path('test-paper', testPaper, name='testpaper'),
    path('calculate-result', calculateTestResult, name='calculateTest'),
    path('test-history', testResultHistory, name='testHistory'),
    path('result', showTestResult, name='result'),
    path('logout', logoutView, name='logout'),
    path('delete-account', deleteAccountView, name='deleteAccount'),
    path('membership', membershipPlansView, name='membership'),
]
