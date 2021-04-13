from django.contrib import admin

from .models import ActionType, Entry, History, Route


admin.site.register(ActionType)
admin.site.register(Entry)
admin.site.register(History)
admin.site.register(Route)
