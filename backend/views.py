from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Profile


def index(request):
    return JsonResponse({"message": "API root node"})

@csrf_exempt
def register(request):
    response = {'error': ''}
    if request.method == "POST":
        try:
            User.objects.get(username=request.POST['username'])
            response['error'] = 'username already exists'
        except User.DoesNotExist:
            user = User.objects.create(username=request.POST['username'], password=request.POST['password'])
            user.save()
            response['token'] = user.profile.token
    else:
        response['error'] = 'invalid request'
    return JsonResponse(response)

@csrf_exempt
def login(request):
    response = {'error': ''}
    if request.method == "POST":
        try:
            user = User.objects.get(username=request.POST['username'], password=request.POST['password'])
            if user.profile.expired:
                user.profile.new_token()
            response['token'] = user.profile.token
        except User.DoesNotExist:
            response['error'] = 'invalid login'
    else:
        response['error'] = 'invalid request'
    return JsonResponse(response)

@csrf_exempt
def logout(request):
    response = {'error': ''}
    if request.method == "POST":
        pass
    else:
        response['error'] = 'invalid request'
    return JsonResponse(response)

def me(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        response['data'] = {
            "nick": profile.user.username,
            "personality": {
                "fire": {"value": 0.678, "positive": True},
                "water": {"value": 0.678, "positive": False},
                "earth": {"value": 0.678, "positive": True},
                "air": {"value": 0.678, "positive": False},
                "space": {"value": 0.678, "positive": True},
            },
            "interests": [
                {"name": "Coding", "amount": 3},
                {"name": "Entrepreneurship", "amount": 2},
                {"name": "TV Shows", "amount": 1},
            ],
        } # dummy data
    return JsonResponse(response)

def get_profile(request, response):
    splits = request.META['HTTP_AUTHORIZATION'].split("Bearer ")
    if len(splits) == 2 and splits[0] == "":
        token = splits[1]
        try:
            profile = Profile.objects.get(token=token)
            if profile.expired:
                response['error'] = 'token expired'
            else:
                return profile
        except Profile.DoesNotExist:
            response['error'] = 'invalid token'
    else:
        response['error'] = 'invalid header'
