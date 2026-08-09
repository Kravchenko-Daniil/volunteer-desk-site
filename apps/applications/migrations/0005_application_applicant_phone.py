from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0004_submissionattempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='applicant_phone',
            field=models.CharField(blank=True, max_length=32, verbose_name='Телефон заявителя'),
        ),
    ]
