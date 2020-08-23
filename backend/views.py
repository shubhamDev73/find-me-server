import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .decorators import auth
from .models import Profile, Interest, UserInterest, Question, Answer, AvatarBase, Mood, Avatar, Access, Connect


MAX_PROFILE_VIEWS = 1

def index(request):
    return {"message": "API root node"}

@csrf_exempt
def register(request):
    token = None
    error = ''
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        try:
            User.objects.get(username=data['username'])
            error = 'username already exists'
        except User.DoesNotExist:
            user = User.objects.create(username=data['username'])
            user.set_password(data['password'])
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
        data = json.loads(request.body.decode("utf-8"))
        try:
            user = User.objects.get(username=data['username'])
            if user.check_password(data['password']):
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
        "avatar": request.profile.avatar.url,
        "personality": {
            "fire": {"value": 0.678, "positive": True},
            "water": {"value": 0.678, "positive": False},
            "earth": {"value": 0.678, "positive": True},
            "air": {"value": 0.678, "positive": False},
            "space": {"value": 0.678, "positive": True},
        }, # dummy data
        "interests": [{"name": user_interest.interest.name, "amount": user_interest.amount} for user_interest in UserInterest.objects.filter(user=request.profile.user) ],
        "mood": request.profile.avatar.mood.name,
    }

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

@csrf_exempt
@auth
def update_interests(request):
    data = json.loads(request.body.decode("utf-8"))
    interests = [int(interest) for interest in data['interests'].split(',')]
    amounts = [int(amount) for amount in data.get('amounts', '0').split(',')]
    remove = data.__contains__('remove')
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

@csrf_exempt
@auth
def update_interest(request, pk):
    data = json.loads(request.body.decode("utf-8"))
    question = Question.objects.get(pk=data['question'])
    user_interest = UserInterest.objects.get(user=request.profile.user, interest=pk)
    text = data['answer']
    try:
        answer = Answer.objects.get(user_interest=user_interest, question=question)
        answer.text = text
    except Answer.DoesNotExist:
        answer = Answer.objects.create(user_interest=user_interest, question=question, text=text)
    answer.save()

@auth
def me_avatar(request):
    return {
        "url": request.profile.avatar.url,
        "name": request.profile.avatar.base.name,
        "mood": request.profile.avatar.mood.name,
        "base": request.profile.avatar.base.url,
        "variants": [{
            "id": avatar.id,
            "mood": avatar.mood.name,
            "url": avatar.url,
        } for avatar in Avatar.objects.filter(base=request.profile.avatar.base)],
    }

@csrf_exempt
@auth
def me_avatar_update(request):
    data = json.loads(request.body.decode("utf-8"))
    avatar = Avatar.objects.get(pk=data['id'])
    request.profile.avatar = avatar
    request.profile.save()

@auth
def interests(request):
    return [{"id": interest.id, "name": interest.name} for interest in Interest.objects.all()]

@auth
def interest(request, pk):
    interest = Interest.objects.get(pk=pk)
    return {"name": interest.name, "questions": [{"id": question.id, "text": question.text} for question in Question.objects.filter(interest=interest)]}

@auth
def base_avatars(request):
    return [{"id": base.id, "name": base.name, "url": base.url} for base in AvatarBase.objects.all()]

@auth
def avatars(request, pk):
    base = AvatarBase.objects.get(pk=pk)
    return [{"id": avatar.id, "mood": avatar.mood.name, "url": avatar.url} for avatar in Avatar.objects.filter(base=base)]

@auth
def find(request):
    return [{
        "id": access.id,
        "avatar": access.other.avatar.url,
        "mood": access.other.avatar.mood.name,
        "personality": {
            "fire": {"value": 0.678, "positive": True},
            "water": {"value": 0.678, "positive": False},
        }, # dummy data
    } for access in Access.objects.filter(me=request.profile)]

@csrf_exempt
@auth
def view(request):
    data = json.loads(request.body.decode("utf-8"))
    access = Access.objects.get(pk=data['id'])
    if access.me == request.profile:
        if not access.viewed:
            if MAX_PROFILE_VIEWS and Access.objects.filter(me=request.profile).filter(viewed=True).count() >= MAX_PROFILE_VIEWS:
                return {'error': 'max profile views exceeded'}
            access.viewed = True
            access.save()
        return {
            "nick": access.other.user.username,
            "avatar": access.other.avatar.url,
            "personality": {
                "fire": {"value": 0.678, "positive": True},
                "water": {"value": 0.678, "positive": False},
                "earth": {"value": 0.678, "positive": True},
                "air": {"value": 0.678, "positive": False},
                "space": {"value": 0.678, "positive": True},
            }, # dummy data
            "interests": [{"name": user_interest.interest.name, "amount": user_interest.amount} for user_interest in UserInterest.objects.filter(user=access.other.user) ],
            "mood": access.other.avatar.mood.name,
        }
    else:
        return {'error': 'invalid view'}

@csrf_exempt
@auth
def request(request):
    data = json.loads(request.body.decode("utf-8"))
    access = Access.objects.get(pk=data['id'])
    if access.me == request.profile and access.viewed:
        if access.requested:
            return {'error': 'already requested'}
        access.requested = True
        access.save()
    else:
        return {'error': 'invalid request'}

@auth
def requests(request):
    return [{
        "id": access.id,
        "avatar": access.me.avatar.url,
    } for access in Access.objects.filter(other=request.profile).filter(requested=True).filter(connected=False)]

@csrf_exempt
@auth
def accept(request):
    data = json.loads(request.body.decode("utf-8"))
    access = Access.objects.get(pk=data['id'])
    if access.other == request.profile and access.requested:
        if access.connected:
            return {'error': 'request already accepted'}
        access.connected = True
        access.save()
        connect = Connect.objects.create(user1=access.me, user2=access.other)
        connect.save()
    else:
        return {'error': 'invalid accept'}

@auth
def found(request):
    connects = [(connect.user2, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user1=request.profile)]
    connects += [(connect.user1, connect.retained1 and connect.retained2) for connect in Connect.objects.filter(user2=request.profile)]
    return [{
        "nick": profile.user.username,
        "avatar": profile.avatar.url,
        "retained": retained
    } for profile, retained in connects]
