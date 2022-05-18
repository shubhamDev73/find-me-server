from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import *


admin.site.site_title = "Find Me"
admin.site.site_header = "Find Me - Admin Panel"

class BaseModelAdmin(admin.ModelAdmin):

    def get_link(self, url):
        return format_html(f'<a href="{url}" target="_blank">{url}</a>')

    def get_image(self, url):
        return format_html(f'<a href="{url}" target="_blank"><img src="{url}" alt="{url}" height="100"></a>')

    def get_fields(self, request, obj=None):
        if not (fields := self.fields):
            fields = super().get_fields(request, obj)
        try:
            return fields if obj else self.add_fields
        except:
            return fields

    def get_readonly_fields(self, request, obj=None):
        if not (fields := self.readonly_fields):
            fields = super().get_readonly_fields(request, obj)
        try:
            return fields if obj else (set(fields) - set(self.add_fields))
        except:
            return fields

class InfoModelAdmin(BaseModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

class UserInfoModelAdmin(InfoModelAdmin):

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(User)
class NewUserAdmin(UserAdmin):

    list_display = ['id', 'username', 'email', 'phone', 'expired']

    def expire_tokens(self, request, queryset):
        queryset.update(expired=True, fcm_token='')
    expire_tokens.short_description = 'Expire auth tokens'

    actions = [expire_tokens]

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
class ProfileAdmin(UserInfoModelAdmin):

    def mood(self, obj):
        return str(obj.avatar.mood) if obj.avatar else None

    def base_avatar(self, obj):
        return str(obj.avatar.base) if obj.avatar else None

    list_display = fields = ['user', 'personality', 'last_questionnaire_time', 'base_avatar', 'mood', 'onboarded']
    list_filter = [AvatarBaseListFilter, 'avatar__mood']
    search_fields = ['user__username', 'avatar__base__name', 'avatar__mood__name']

@admin.register(Personality)
class PersonalityAdmin(BaseModelAdmin):

    def has_add_permission(self, request, obj=None):
        return False

    def url_as_link(self, url):
        return f'<a href="{url}" target="_blank">{url}</a>'

    def link(self, obj):
        return format_html(', '.join(self.url_as_link(url) for url in obj.get_urls()))

    list_display = ['trait', 'display_name', 'description', 'link']
    readonly_fields = ['trait']
    list_filter = ['trait', 'display_name']
    search_fields = ['trait', 'display_name', 'description']

@admin.register(Adjective)
class AdjectiveAdmin(BaseModelAdmin):

    fields = list_display = ['name', 'trait', 'facet', 'pool', 'description']
    list_filter = ['trait', 'facet', 'pool']
    search_fields = ['name', 'description']

@admin.register(PersonalityQuestionnaire)
class PersonalityQuestionnaireAdmin(BaseModelAdmin):

    def link(self, obj):
        return format_html(f'<a href="{obj.url}" target="_blank">{obj.url}</a>')

    list_display = ['id', 'link', 'initial']
    list_filter = ['initial']
    search_fields = ['url']

@admin.register(Interest)
class InterestAdmin(BaseModelAdmin):

    search_fields = ['name']

@admin.register(UserInterest)
class UserInterestAdmin(UserInfoModelAdmin):

    list_display = ['user', 'interest', 'amount', 'last_change']
    list_filter = ['interest', 'amount', 'user']
    search_fields = ['user__username', 'interest__name']

@admin.register(Question)
class QuestionAdmin(BaseModelAdmin):

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
class AnswerAdmin(UserInfoModelAdmin):

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
class AvatarBaseAdmin(BaseModelAdmin):

    def link(self, obj):
        return self.get_image(obj.url)

    list_display = ['name', 'link']
    search_fields = ['name', 'url']

@admin.register(Mood)
class MoodAdmin(BaseModelAdmin):

    def weather_image(self, obj):
        return self.get_image(obj.get_url('weather'))
    def icon_image(self, obj):
        return self.get_image(obj.get_url('icon'))

    list_display = ['name', 'weather_image', 'icon_image']
    search_fields = ['name', 'weather', 'icon']

@admin.register(Avatar)
class AvatarAdmin(BaseModelAdmin):

    def icon_image(self, obj):
        return self.get_image(obj.get_url('v1'))
    def main_image(self, obj):
        return self.get_image(obj.get_url('v2'))

    list_display = ['base', 'mood', 'icon_image', 'main_image']
    list_filter = ['base__name', 'mood']
    search_fields = ['base__name', 'mood__name']

@admin.register(AvatarTimeline)
class AvatarTimelineAdmin(UserInfoModelAdmin):

    list_display = ['user', 'avatar', 'timestamp']
    list_filter = ['user', 'avatar__base', 'avatar__mood']
    search_fields = ['user__username', 'avatar__base__name', 'avatar__mood__name']
    date_hierarchy = 'timestamp'

@admin.register(Access)
class AccessAdmin(InfoModelAdmin):

    def expire_access(self, request, queryset):
        queryset.update(active=False)
    expire_access.short_description = 'Expire accesses'

    readonly_fields = ['id', 'me', 'other', 'create_time', 'viewed', 'view_time', 'requested', 'request_time', 'connected', 'connect_time']
    fields = ['active'] + readonly_fields
    list_display = readonly_fields + ['active']
    add_fields = ['me', 'other', 'active']
    list_filter = ['active', 'viewed', 'requested', 'connected', 'me', 'other']
    search_fields = ['me__user__username', 'other__user__username', 'create_time', 'view_time', 'request_time', 'connect_time']
    date_hierarchy = 'create_time'
    actions = [expire_access]

@admin.register(Connect)
class ConnectAdmin(InfoModelAdmin):

    def expire_connect(self, request, queryset):
        queryset.update(active=False)
    expire_connect.short_description = 'Expire connects'

    readonly_fields = ['id', 'user1', 'user2', 'chat_id', 'create_time', 'block', 'retained1', 'retain1_time', 'retained2', 'retain2_time', 'retained', 'retain_time']
    fields = ['active'] + readonly_fields
    list_display = readonly_fields + ['active']
    add_fields = ['user1', 'user2', 'active']
    list_filter = ['active', 'retained1', 'retained2', 'user1', 'user2']
    search_fields = ['user1__user__username', 'user2__user__username', 'create_time', 'retain1_time', 'retain2_time', 'retain_time']
    date_hierarchy = 'create_time'
    actions = [expire_connect]
