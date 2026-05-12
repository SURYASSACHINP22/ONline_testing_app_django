from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OTS', '0005_membership_allowed_test_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='password',
            field=models.CharField(max_length=128),
        ),
    ]
