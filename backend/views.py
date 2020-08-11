from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
