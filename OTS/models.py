from django.db import models

# Create your models here.


class MembershipPlan(models.Model):
    """Membership plan: controls which test types (question counts) a user can take."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    # Comma-separated allowed test sizes, e.g. "1,3,5" = can take 1-, 3-, or 5-question tests
    allowed_question_counts = models.CharField(
        max_length=50, default='1,3,5',
        help_text='Comma-separated test sizes, e.g. 1,3,5 (only these question counts are allowed)'
    )
    max_tests_per_day = models.PositiveIntegerField(null=True, blank=True, help_text='Null = unlimited')
    order = models.PositiveSmallIntegerField(default=0, help_text='Display order (lower first)')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_allowed_question_counts(self):
        """Return list of integers allowed for this plan, e.g. [1, 3, 5]. Blank = allow default 1,3,5."""
        if not self.allowed_question_counts or not self.allowed_question_counts.strip():
            return [1, 3, 5]
        out = []
        for part in self.allowed_question_counts.split(','):
            part = part.strip()
            if part.isdigit():
                out.append(int(part))
        return sorted(set(out)) if out else [1, 3, 5]


class Candidate(models.Model):
    username = models.CharField(primary_key=True, max_length=20)
    password = models.CharField(null=False, max_length=20)
    name = models.CharField(null=False, max_length=30)
    test_attempted = models.IntegerField(default=0)
    points = models.FloatField(default=0.0)
    membership_plan = models.ForeignKey(
        MembershipPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates'
    )

    def __str__(self):
        return self.username

class Question(models.Model):
    qid = models.BigAutoField(primary_key=True,auto_created=True)
    que = models.TextField()
    a = models.CharField(max_length=255)
    b = models.CharField(max_length=255)
    c = models.CharField(max_length=255)
    d = models.CharField(max_length=255)
    ans = models.CharField(max_length=2)


class Result(models.Model):
    resultid = models.AutoField(primary_key=True)
    username = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    attempt = models.IntegerField(default=0)
    right = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)
    points = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-date']  # Most recent first

    def __str__(self):
        return f"{self.username} - {self.date}"
