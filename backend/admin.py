from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    fields = ['user']
    list_display = ['user', 'expired']

    def expire_tokens(self, request, queryset):
        queryset.update(expired=True)
    expire_tokens.short_description = 'Expire auth tokens'

    actions = [expire_tokens]
