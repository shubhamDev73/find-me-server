from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Profile, Connect


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
            user = User.objects.create(username=request.POST['username'])
            user.set_password(request.POST['password'])
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
            user = User.objects.get(username=request.POST['username'])
            if user.check_password(request.POST['password']):
                if user.profile.expired:
                    user.profile.new_token()
                response['token'] = user.profile.token
            else:
                response['error'] = 'invalid password'
        except User.DoesNotExist:
            response['error'] = 'not registered'
    else:
        response['error'] = 'invalid request'
    return JsonResponse(response)

@csrf_exempt
def logout(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        profile.expired = True
        profile.save()
    return JsonResponse(response)

def me(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        response['data'] = {
            "nick": profile.user.username,
            "avatar": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
            "avatar-base": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
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
            "mood": "cheerful",
        } # dummy data
    return JsonResponse(response)

def found(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        connects = [(connect.user2, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user1=profile)]
        connects += [(connect.user1, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user2=profile)]
        response['data'] = [{
            "nick": profile.user.username,
            "avatar": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
            "retained": retained
        } for profile, retained in connects]
    return JsonResponse(response)

def get_profile(request, response):
    try:
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
    except:
        response['error'] = 'invalid authorization'
