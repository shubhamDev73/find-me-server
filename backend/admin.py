from django.contrib import admin
from django.utils.html import format_html

from .models import *


admin.site.site_title = "Find Me"
admin.site.site_header = "Find Me - Admin Panel"

class AvatarBaseListFilter(admin.SimpleListFilter):
    title = 'avatar'
    parameter_name = 'avatar__base__name'

    def lookups(self, request, model_admin):
        return ((base.name, base.name) for base in AvatarBase.objects.all())

    def queryset(self, request, queryset):
        if value := self.value():
            return queryset.filter(avatar__base__name=value)
        else:
            return queryset

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    def mood(self, obj):
        return str(obj.avatar.mood)

    def base_avatar(self, obj):
        return str(obj.avatar.base)

    fields = ['expired']
    list_display = ['user', 'personality', 'base_avatar', 'mood', 'expired']
    list_filter = [AvatarBaseListFilter, 'avatar__mood', 'expired']
    search_fields = ['user__username', 'avatar__base__name', 'avatar__mood__name']

    def expire_tokens(self, request, queryset):
        queryset.update(expired=True)
    expire_tokens.short_description = 'Expire auth tokens'

    actions = [expire_tokens]

@admin.register(PersonalityQuestionnaire)
class PersonalityQuestionnaireAdmin(admin.ModelAdmin):

    fields = ['user']
    list_display = ['user', 'create_time', 'submitted', 'submit_time']
    list_filter = ['submitted', 'user']
    search_fields = ['user__username']
    date_hierarchy = 'create_time'
    show_full_result_count = True
    empty_value_display = '<em>-NA-</em>'

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):

    search_fields = ['name']

@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):

    list_display = ['user', 'interest', 'amount']
    list_filter = ['interest', 'amount', 'user']
    search_fields = ['user__username', 'interest__name']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    def question(self, obj):
        return obj.text
    question.short_description = 'Question'

    list_display = ['interest', 'question']
    list_filter = ['interest']
    search_fields = ['interest__name', 'text']

class QuestionTextListFilter(admin.SimpleListFilter):
    title = 'question'
    parameter_name = 'question__text'

    def lookups(self, request, model_admin):
        return ((question.text, question.text) for question in Question.objects.all())

    def queryset(self, request, queryset):
        if value := self.value():
            return queryset.filter(question__text=value)
        else:
            return queryset

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):

    def user(self, obj):
        return str(obj.user_interest.user)

    def interest(self, obj):
        return str(obj.user_interest.interest)

    def question_text(self, obj):
        return obj.question.text
    question_text.short_description = 'Question'

    def answer(self, obj):
        return obj.text
    answer.short_description = 'Answer'

    list_display = ['user', 'interest', 'question_text', 'answer']
    list_filter = ['user_interest__interest', QuestionTextListFilter, 'user_interest__user']
    search_fields = ['user_interest__user__username', 'user_interest__interest__name', 'question__text', 'text']

@admin.register(AvatarBase)
class AvatarBaseAdmin(admin.ModelAdmin):

    def link(self, obj):
        return format_html(f'<a href="{obj.url}" target="_blank">{obj.url}</a>')

    list_display = ['name', 'link']
    search_fields = ['name', 'url']

@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):

    search_fields = ['name']

@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):

    def link(self, obj):
        return format_html(f'<a href="{obj.url}" target="_blank">{obj.url}</a>')

    list_display = ['base', 'mood', 'link']
    list_filter = ['base__name', 'mood']
    search_fields = ['base__name', 'mood__name', 'url']

@admin.register(Access)
class AccessAdmin(admin.ModelAdmin):

    fields = ['me', 'other', 'active']
    list_display = ['id', 'me', 'other', 'create_time', 'active', 'viewed', 'view_time', 'requested', 'request_time', 'connected', 'connect_time']
    list_filter = ['active', 'viewed', 'requested', 'connected', 'me', 'other']
    search_fields = ['me__user__username', 'other__user__username', 'create_time', 'view_time', 'request_time', 'connect_time']
    date_hierarchy = 'create_time'

    def expire_access(self, request, queryset):
        queryset.update(active=False)
    expire_access.short_description = 'Expire accesses'

    actions = [expire_access]

@admin.register(Connect)
class ConnectAdmin(admin.ModelAdmin):

    fields = ['user1', 'user2', 'active']
    list_display = ['id', 'user1', 'user2', 'create_time', 'active', 'retained1', 'retain1_time', 'retained2', 'retain2_time', 'retained', 'retain_time']
    list_filter = ['active', 'retained1', 'retained2', 'user1', 'user2']
    search_fields = ['user1__user__username', 'user2__user__username', 'create_time', 'retain1_time', 'retain2_time', 'retain_time']
    date_hierarchy = 'create_time'

    def expire_connect(self, request, queryset):
        queryset.update(active=False)
    expire_connect.short_description = 'Expire connects'

    actions = [expire_connect]
