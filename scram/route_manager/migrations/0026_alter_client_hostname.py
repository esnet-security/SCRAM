# Generated by Django 3.2.13 on 2023-02-09 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0025_rename_uuid_client_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="client",
            name="hostname",
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
