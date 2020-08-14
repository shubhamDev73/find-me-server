from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Profile, Interest, UserInterest, Question, Answer, Connect


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
            "interests": [{"name": user_interest.interest.name, "amount": user_interest.amount} for user_interest in UserInterest.objects.filter(user=profile.user) ],
            "mood": "cheerful",
        } # dummy data
    return JsonResponse(response)

def me_interests(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        response['data'] = []
        user_interests = UserInterest.objects.filter(user=profile.user)
        for user_interest in user_interests:
            response['data'].append({
                "name": user_interest.interest.name,
                "amount": user_interest.amount,
                "answers": [{"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)]
            })
    return JsonResponse(response)

def interests(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        response['data'] = [{"id": interest.id, "name": interest.name} for interest in Interest.objects.all()]
    return JsonResponse(response)

def update_interests(request):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        interests = [int(interest) for interest in request.GET['interests'].split(',')]
        amounts = [int(amount) for amount in request.GET.get('amounts', '0').split(',')]
        remove = request.GET.__contains__('remove')
        user_interests = UserInterest.objects.filter(user=profile.user, interest__in=interests)
        if remove:
            user_interests.delete()
        else:
            for user_interest in user_interests:
                index = interests.index(user_interest.interest.pk)
                user_interest.amount = amounts[index]
                user_interest.save()
                amounts[index] = 0
            for index, amount in enumerate(amounts):
                if amount != 0:
                    interest = Interest.objects.get(pk=interests[index])
                    user_interest = UserInterest.objects.create(user=profile.user, interest=interest, amount=amount)
                    user_interest.save()
    return JsonResponse(response)

def update_interest(request, pk):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        question = Question.objects.get(pk=request.GET['question'])
        user_interest = UserInterest.objects.get(user=profile.user, interest=pk)
        text = request.GET['answer']
        try:
            answer = Answer.objects.get(user_interest=user_interest, question=question)
            answer.text = text
        except Answer.DoesNotExist:
            answer = Answer.objects.create(user_interest=user_interest, question=question, text=text)
        answer.save()
    return JsonResponse(response)

def interest(request, pk):
    response = {'error': ''}
    profile = get_profile(request, response)
    if profile:
        interest = Interest.objects.get(pk=pk)
        response['data'] = {"name": interest.name, "questions": [{"id": question.id, "text": question.text} for question in Question.objects.filter(interest=interest)]}
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
