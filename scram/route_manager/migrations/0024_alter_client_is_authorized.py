# Generated by Django 3.2.13 on 2023-02-09 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0023_client"),
    ]

    operations = [
        migrations.AlterField(
            model_name="client",
            name="is_authorized",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
