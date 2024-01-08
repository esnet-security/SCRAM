
from django.db import migrations


def create(apps, schema_editor):
    ActionType = apps.get_model("route_manager", "ActionType")
    at = ActionType.objects.get(name="block")

    WebSocketMessage = apps.get_model("route_manager", "WebSocketMessage")
    wsm = WebSocketMessage(msg_type="translator_add", msg_data_route_field="route")
    wsm.save()

    WebSocketSequenceElement = apps.get_model("route_manager", "WebSocketSequenceElement")
    wsse = WebSocketSequenceElement(websocketmessage=wsm, verb="A", action_type=at)
    wsse.save()


class Migration(migrations.Migration):

    dependencies = [
        ("route_manager", "0027_websocketmessage_websocketsequenceelement"),
    ]

    operations = [
        migrations.RunPython(create),
    ]
