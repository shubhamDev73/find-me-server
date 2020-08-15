from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .decorators import auth
from .models import Profile, Interest, UserInterest, Question, Answer, Connect


def index(request):
    return {"message": "API root node"}

@csrf_exempt
def register(request):
    token = None
    error = ''
    if request.method == "POST":
        try:
            User.objects.get(username=request.POST['username'])
            error = 'username already exists'
        except User.DoesNotExist:
            user = User.objects.create(username=request.POST['username'])
            user.set_password(request.POST['password'])
            user.save()
            token = user.profile.token
    else:
        error = 'invalid request'
    return {'token': token, 'error': error}

@csrf_exempt
def login(request):
    token = None
    error = ''
    if request.method == "POST":
        try:
            user = User.objects.get(username=request.POST['username'])
            if user.check_password(request.POST['password']):
                if user.profile.expired:
                    user.profile.new_token()
                token = user.profile.token
            else:
                error = 'invalid password'
        except User.DoesNotExist:
            error = 'not registered'
    else:
        error = 'invalid request'
    return {'token': token, 'error': error}

@csrf_exempt
@auth
def logout(request):
    request.profile.expired = True
    request.profile.save()

@auth
def me(request):
    return {
        "nick": request.profile.user.username,
        "avatar": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
        "avatar-base": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
        "personality": {
            "fire": {"value": 0.678, "positive": True},
            "water": {"value": 0.678, "positive": False},
            "earth": {"value": 0.678, "positive": True},
            "air": {"value": 0.678, "positive": False},
            "space": {"value": 0.678, "positive": True},
        },
        "interests": [{"name": user_interest.interest.name, "amount": user_interest.amount} for user_interest in UserInterest.objects.filter(user=request.profile.user) ],
        "mood": "cheerful",
    } # dummy data

@auth
def me_interests(request):
    interests = []
    user_interests = UserInterest.objects.filter(user=request.profile.user)
    for user_interest in user_interests:
        interests.append({
            "name": user_interest.interest.name,
            "amount": user_interest.amount,
            "answers": [{"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)]
        })
    return interests

@auth
def interests(request):
    return [{"id": interest.id, "name": interest.name} for interest in Interest.objects.all()]

@auth
def update_interests(request):
    interests = [int(interest) for interest in request.GET['interests'].split(',')]
    amounts = [int(amount) for amount in request.GET.get('amounts', '0').split(',')]
    remove = request.GET.__contains__('remove')
    user_interests = UserInterest.objects.filter(user=request.profile.user, interest__in=interests)
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
                user_interest = UserInterest.objects.create(user=request.profile.user, interest=interest, amount=amount)
                user_interest.save()

@auth
def update_interest(request, pk):
    question = Question.objects.get(pk=request.GET['question'])
    user_interest = UserInterest.objects.get(user=request.profile.user, interest=pk)
    text = request.GET['answer']
    try:
        answer = Answer.objects.get(user_interest=user_interest, question=question)
        answer.text = text
    except Answer.DoesNotExist:
        answer = Answer.objects.create(user_interest=user_interest, question=question, text=text)
    answer.save()

@auth
def interest(request, pk):
    interest = Interest.objects.get(pk=pk)
    return {"name": interest.name, "questions": [{"id": question.id, "text": question.text} for question in Question.objects.filter(interest=interest)]}

@auth
def found(request):
    connects = [(connect.user2, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user1=request.profile)]
    connects += [(connect.user1, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user2=request.profile)]
    return [{
        "nick": profile.user.username,
        "avatar": "https://media.vanityfair.com/photos/5ba12e6b6603312e2a5bbee8/master/w_768,c_limit/Avatar-The-Last-Airbender-Live-Action.jpg",
        "retained": retained
    } for profile, retained in connects]
