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
    class Meta:
        model = Candidate
        fields = ['name']


class QuestionSerializer(serializers.ModelSerializer):
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