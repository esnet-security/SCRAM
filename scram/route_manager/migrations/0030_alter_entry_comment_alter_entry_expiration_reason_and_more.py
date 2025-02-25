# Generated by Django 4.2.17 on 2024-12-24 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0029_alter_websocketmessage_msg_data_route_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entry",
            name="comment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="entry",
            name="expiration_reason",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Optional reason for the expiration",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="historicalentry",
            name="comment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="historicalentry",
            name="expiration_reason",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Optional reason for the expiration",
                max_length=200,
            ),
        ),
    ]
