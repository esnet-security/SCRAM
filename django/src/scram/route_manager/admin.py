"""Register models in the Admin site."""

from django.contrib import admin, messages
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    ActionType,
    Client,
    Entry,
    IgnoreEntry,
    Route,
    TranslatorType,
)


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


class NameLockedAfterCreate(admin.ModelAdmin):
    """Mixin to make the name field read-only once saved."""

    def get_readonly_fields(self, request, obj=None) -> list[str]:
        """Add name to the read-only fields for existing objects."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # i.e. the object already exists so you shouldn't be allowed to change the name.
            readonly.append("name")
        return readonly


@admin.register(ActionType)
class ActionTypeAdmin(NameLockedAfterCreate, SimpleHistoryAdmin):
    """Configure the ActionType and how it shows up in the Admin site."""

    list_filter = ("available",)
    list_display = ("name", "available")
    filter_horizontal = ("translator_types",)
    readonly_fields = ("message_types", "translator_urls")

    @admin.display(description="Message types sent by this action")
    def message_types(self, obj):
        """Show the message types translators receive for this action."""
        return (
            ", ".join(obj.message_type(verb) for verb in ActionType.VERBS)
            if obj.pk
            else "-"
        )

    @admin.display(description="Translator URLs Receiving This Action")
    def translator_urls(self, obj):
        """Show where the translators for this action should connect."""
        return ", ".join(tt.url for tt in obj.translator_types.all()) if obj.pk else "-"

    def save_related(self, request, form, formsets, change):
        """Makes sure that translators are updated when an action type is linked/unlinked from a translator type.

        This works by calling .send_active_entries() on all action_type objects that were touched.
        """

        before = set(form.instance.translator_types.all())
        super().save_related(request, form, formsets, change)
        after = set(form.instance.translator_types.all())

        if after - before:  # A translator was linked to this action_type
            form.instance.send_active_entries("add", after - before)
        if before - after:  # a translator was unlinked from this action_type
            form.instance.send_active_entries("remove", before - after)
        if not after:
            messages.warning(
                request,
                f"No translator types are linked to {form.instance.name}, so its entries won't be sent anywhere.",
            )


@admin.register(TranslatorType)
class TranslatorTypeAdmin(NameLockedAfterCreate, SimpleHistoryAdmin):
    """Show each translator type's websocket URL."""

    list_display = ("name", "url")
    readonly_fields = ("url",)

    @staticmethod
    def withdraw(translator_type) -> None:
        """Send removes for every active entry this translator type carries out; its links are deleted with it."""
        for actiontype in translator_type.actiontype_set.all():
            actiontype.send_active_entries("remove", [translator_type])

    def delete_model(self, request, obj) -> None:
        """Withdraw a specific translator type's routes before deleting it."""
        self.withdraw(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset) -> None:
        """Withdraw routes for every translator type in a bulk delete."""
        for translator_type in queryset:
            self.withdraw(translator_type)
        super().delete_queryset(request, queryset)


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
    """Configure the Client and how it shows up in the Admin site."""

    list_display = ("client_name", "uuid")
    readonly_fields = ("uuid",)


admin.site.register(IgnoreEntry, SimpleHistoryAdmin)
admin.site.register(Route)
