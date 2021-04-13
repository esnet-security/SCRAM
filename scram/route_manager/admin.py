from django.contrib import admin

from .models import ActionType, Entry, Route


admin.site.register(Route)
admin.site.register(ActionType)
admin.site.register(Entry)
