# Generated manually for submitted_by (user who logged the labor)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apps', '0004_clientcompany_house'),
    ]

    operations = [
        migrations.AddField(
            model_name='technicianlabor',
            name='submitted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='submitted_labor_entries',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
