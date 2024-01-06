# Generated by Django 3.1.7 on 2021-04-13 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0006_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="history",
            name="expiration",
            field=models.DateTimeField(default="9999-12-31"),
        ),
        migrations.AddField(
            model_name="history",
            name="expiration_reason",
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name="Optional reason for the expiration"
            ),
        ),
    ]
