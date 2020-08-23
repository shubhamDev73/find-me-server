from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),


    path('me/', views.me, name='me'),

    path('me/interests/', views.me_interests, name='me_interests'),
    path('me/interests/update/', views.update_interests, name='update_interests'),
    path('me/interests/<int:pk>/update/', views.update_interest, name='update_interest'),

    path('me/avatar/', views.me_avatar, name='me_avatar'),
    path('me/avatar/update/', views.me_avatar_update, name='me_avatar_update'),


    path('interests/', views.interests, name='interests'),
    path('interests/<int:pk>/', views.interest, name='interest'),

    path('avatars/', views.base_avatars, name='base_avatars'),
    path('avatars/<int:pk>/', views.avatars, name='avatars'),


    path('find/', views.find, name='find'),
    path('find/view/', views.view, name='view'),
    path('find/request/', views.request, name='request'),

    path('requests/', views.requests, name='requests'),
    path('requests/accept/', views.accept, name='accept'),

    path('found/', views.found, name='found'),
    path('found/retain/', views.retain, name='retain'),
]
