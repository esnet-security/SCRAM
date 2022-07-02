from django.contrib import admin

from .models import ActionType, Entry, History, IgnoreEntry, Route


@admin.register(ActionType)
class ActionTypeAdmin(admin.ModelAdmin):
    list_filter = ("available",)
    list_display = ("name", "available")


admin.site.register(Entry)
admin.site.register(History)
admin.site.register(IgnoreEntry)
admin.site.register(Route)
