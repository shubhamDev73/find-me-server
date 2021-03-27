from django.urls import path, include

from . import views


app_name = 'api'

urls_auth = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]

urls_interests = [
    path('', views.interests, name='index'),
    path('<int:pk>/', views.interest, name='interest'),
]

urls_avatars = [
    path('', views.base_avatars, name='index'),
    path('<int:pk>/', views.avatars, name='avatars'),
]

urls_data = [
    path('interests/', include(urls_interests), name='interests'),
    path('avatars/', include(urls_avatars), name='avatars'),
    path('moods/', views.moods, name='moods'),
]

urls_me = [
    path('', views.me, name='index'),

	path('personality/', views.personality, name='personality'),
    path('personality/update/', views.personality_update, name='personality_update'),

    path('interests/', views.me_interests, name='interests'),
    path('interests/update/', views.update_interests, name='update_interests'),
    path('interests/<int:pk>/', views.me_interest, name='interest'),
    path('interests/<int:pk>/update/', views.update_interest, name='update_interest'),

    path('avatar/', views.me_avatar, name='avatar'),
    path('avatar/update/', views.me_avatar_update, name='avatar_update'),
]

urls_find = [
    path('', views.find, name='index'),
    path('<int:pk>/', views.find_view, name='view'),
    path('request/', views.request, name='request'),
]

urls_views = [
    path('', views.views, name='index'),
    path('<int:pk>/', views.view_view, name='view'),
]

urls_requests = [
    path('', views.requests, name='index'),
    path('<int:pk>/', views.request_view, name='view'),
    path('accept/', views.accept, name='accept'),
]

urls_found = [
    path('', views.found, name='index'),
    path('<int:pk>/', views.found_view, name='view'),
    path('read/', views.found_read, name='read'),
    path('retain/', views.retain, name='retain'),
]

urls_notification = [
    path('token/', views.notification_token, name='token'),
]

urlpatterns = [
    path('', views.index, name='index'),
    path('', include(urls_auth), name='auth'),
    path('', include(urls_data), name='data'),
    path('me/', include(urls_me), name='me'),
    path('find/', include(urls_find), name='find'),
    path('views/', include(urls_views), name='views'),
    path('requests/', include(urls_requests), name='requests'),
    path('found/', include(urls_found), name='found'),
    path('notification/', include(urls_notification), name='notification'),
]
