"""Register models in the Admin site."""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ActionType, Client, Entry, IgnoreEntry, Route, WebSocketMessage, WebSocketSequenceElement


@admin.register(ActionType)
class ActionTypeAdmin(SimpleHistoryAdmin):
    """Configure the ActionType and how it shows up in the Admin site."""

    list_filter = ("available",)
    list_display = ("name", "available")


admin.site.register(Entry, SimpleHistoryAdmin)
admin.site.register(IgnoreEntry, SimpleHistoryAdmin)
admin.site.register(Route)
admin.site.register(Client)
admin.site.register(WebSocketMessage)
admin.site.register(WebSocketSequenceElement)
