from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mspcompany",
            name="entra_id_client_secret_id",
            field=models.CharField(
                blank=True,
                help_text="Optional Microsoft Entra ID client secret identifier for operational tracking",
                max_length=255,
                null=True,
            ),
        ),
    ]
