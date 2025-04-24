from django.db import models

# Create your models here.

class Candidate(models.Model):
    username = models.CharField(primary_key = True,max_length=20)
    password = models.CharField(null=False,max_length=20)
    name= models.CharField(null=False,max_length=30)
    test_attempted = models.IntegerField(default=0)
    points = models.FloatField(default=0.0)
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
