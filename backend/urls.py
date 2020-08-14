from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('me/', views.me, name='me'),
    path('me/interests/', views.me_interests, name='me_interests'),
    path('me/update/interests/', views.update_interests, name='update_interests'),
    path('me/update/interests/<int:pk>/', views.update_interest, name='update_interest'),

    path('interests/', views.interests, name='interests'),
    path('interests/<int:pk>/', views.interest, name='interest'),

    path('found/', views.found, name='found'),
]
