from django.contrib import admin

from .models import Profile, Interest, Question, Connect


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    fields = ['user']
    list_display = ['user', 'expired']

    def expire_tokens(self, request, queryset):
        queryset.update(expired=True)
    expire_tokens.short_description = 'Expire auth tokens'

    actions = [expire_tokens]

admin.site.register(Interest)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = ['interest', 'text']

admin.site.register(Connect)
