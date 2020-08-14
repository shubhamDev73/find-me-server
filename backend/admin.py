from django.contrib import admin

from .models import Profile, Interest, UserInterest, Question, Answer, Connect


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    fields = ['user']
    list_display = ['user', 'expired']

    def expire_tokens(self, request, queryset):
        queryset.update(expired=True)
    expire_tokens.short_description = 'Expire auth tokens'

    actions = [expire_tokens]

admin.site.register(Interest)

@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):

    list_display = ['user', 'interest', 'amount']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = ['interest', 'text']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):

    list_display = ['user_interest', 'question', 'text']

admin.site.register(Connect)
