from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Candidate, Result, Question, MembershipPlan


@admin.register(MembershipPlan)
class MembershipPlanAdmin(ModelAdmin):
    list_display = ('name', 'allowed_question_counts', 'max_tests_per_day', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(Candidate)
class CandidateAdmin(ModelAdmin):
    list_display = ('username', 'name', 'membership_plan', 'test_attempted', 'points')
    list_filter = ('membership_plan',)
    list_editable = ('membership_plan',)  # Admin can assign/change plan from list view
    search_fields = ('username', 'name')
    list_select_related = ('membership_plan',)
    list_per_page = 25
    readonly_fields = ('test_attempted', 'points')  # Stats are computed; don't edit by hand
    # "Delete selected" action is built-in; admin can also delete from change form


@admin.register(Result)
class ResultAdmin(ModelAdmin):
    list_display = ('resultid', 'username', 'date', 'attempt', 'right', 'wrong', 'points')
    list_filter = ('username', 'date')
    search_fields = ('username__username', 'username__name')
    list_select_related = ('username',)
    readonly_fields = ('resultid', 'username', 'date', 'attempt', 'right', 'wrong', 'points')
    list_per_page = 50
    date_hierarchy = 'date'


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ('qid', 'que_preview', 'ans')
    list_filter = ()
    search_fields = ('que',)

    def que_preview(self, obj):
        return (obj.que[:60] + '...') if obj.que and len(obj.que) > 60 else (obj.que or '')
    que_preview.short_description = 'Question'
