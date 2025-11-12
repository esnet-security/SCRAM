# Generated manually to replace deprecated index_together with indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0034_alter_entry_originating_scram_instance_and_more"),
    ]

    operations = [
        # HistoricalActionType
        migrations.AlterModelOptions(
            name="historicalactiontype",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical action type",
                "verbose_name_plural": "historical action types",
            },
        ),
        migrations.AddIndex(
            model_name="historicalactiontype",
            index=models.Index(
                fields=["history_date", "id"],
                name="route_manag_history_ee6aeb_idx",
            ),
        ),
        # HistoricalEntry
        migrations.AlterModelOptions(
            name="historicalentry",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical entry",
                "verbose_name_plural": "historical Entries",
            },
        ),
        migrations.AddIndex(
            model_name="historicalentry",
            index=models.Index(
                fields=["history_date", "id"],
                name="route_manag_history_0a19f0_idx",
            ),
        ),
        # HistoricalIgnoreEntry
        migrations.AlterModelOptions(
            name="historicalignoreentry",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical ignore entry",
                "verbose_name_plural": "historical Ignored Entries",
            },
        ),
        migrations.AddIndex(
            model_name="historicalignoreentry",
            index=models.Index(
                fields=["history_date", "id"],
                name="route_manag_history_6909c5_idx",
            ),
        ),
    ]
