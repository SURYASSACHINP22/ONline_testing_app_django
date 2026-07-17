"""
DRF serializers: control which model fields are exposed or writable on the API.

Security ties:
  • QuestionSerializer — omits Question.ans for non-admin list/detail (layer 3).
  • CandidateSerializer / CandidateSelfUpdateSerializer — points & test_attempted not writable
    by self; partial_update in api_views enforces only {name} before save (layer 4).
  • QuestionAdminSerializer — full Question including ans; only used when permissions.is_admin_user.
"""
from rest_framework import serializers
from .models import Candidate, Question, Result, MembershipPlan


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = ['id', 'name', 'description', 'allowed_question_counts', 'max_tests_per_day']


class MembershipPlanAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = '__all__'


class CandidateSerializer(serializers.ModelSerializer):
    membership_plan = MembershipPlanSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = ['username', 'name', 'test_attempted', 'points', 'membership_plan']
        read_only_fields = ['username', 'test_attempted', 'points']


class CandidateAdminSerializer(serializers.ModelSerializer):
    membership_plan = serializers.PrimaryKeyRelatedField(
        queryset=MembershipPlan.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Candidate
        fields = ['username', 'name', 'test_attempted', 'points', 'membership_plan']
        read_only_fields = ['test_attempted', 'points']


class CandidateSelfUpdateSerializer(serializers.ModelSerializer):
    """Used only for PATCH self-profile; fields limited to name — see CandidateViewSet.partial_update."""
    class Meta:
        model = Candidate
        fields = ['name']


class QuestionSerializer(serializers.ModelSerializer):
    """
    Public/candidate API shape for Question. Intentionally omits 'ans' so list/retrieve cannot
    leak correct answers (layer 3). Admin uses QuestionAdminSerializer instead — chosen in
    QuestionViewSet.get_serializer_class() when is_admin_user(request.user).
    """
    class Meta:
        model = Question
        fields = ['qid', 'que', 'a', 'b', 'c', 'd']  # Exclude 'ans' for security


class QuestionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='username.username', read_only=True)

    class Meta:
        model = Result
        fields = ['resultid', 'username', 'date', 'attempt', 'right', 'wrong', 'points']
        read_only_fields = ['resultid', 'username', 'date', 'attempt', 'right', 'wrong', 'points']
