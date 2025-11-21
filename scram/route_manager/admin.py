"""Register models in the Admin site."""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ActionType, Client, Entry, IgnoreEntry, Route, WebSocketMessage, WebSocketSequenceElement


class WhoFilter(admin.SimpleListFilter):
    """Only display users who have added entries in the list_filter."""

    title = "By Username"
    parameter_name = "who"

    # ruff: noqa: PLR6301
    def lookups(self, request, model_admin):
        """Return list of users who have added entries."""
        users_with_entries = Entry.objects.values("who").distinct()

        # If no users have entries, return an empty list so they don't show in filter
        if not users_with_entries:
            return []

        # Return a list of users who have made entries
        return [(user["who"], user["who"]) for user in users_with_entries]

    def queryset(self, request, queryset):
        """Queryset for users."""
        if self.value():
            return queryset.filter(who=self.value())
        return queryset


@admin.register(ActionType)
class ActionTypeAdmin(SimpleHistoryAdmin):
    """Configure the ActionType and how it shows up in the Admin site."""

    list_filter = ("available",)
    list_display = ("name", "available")


@admin.register(Entry)
class EntryAdmin(SimpleHistoryAdmin):
    """Configure how Entries show up in the Admin site."""

    list_select_related = True

    list_filter = [
        "is_active",
        WhoFilter,
    ]
    search_fields = ["route", "comment"]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'uuid', 'registered_from_ip')
    readonly_fields = ('uuid',)


admin.site.register(IgnoreEntry, SimpleHistoryAdmin)
admin.site.register(Route)
admin.site.register(WebSocketMessage)
admin.site.register(WebSocketSequenceElement)
