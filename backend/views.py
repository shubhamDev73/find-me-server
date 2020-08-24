from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils import timezone

from .decorators import auth
from .models import *


MAX_PROFILE_VIEWS = 5

@require_GET
def index(request):
    return {"message": "API root node"}

@require_POST
def register(request):
    token = None
    error = ''
    try:
        user = User.objects.create_user(request.data['username'], password=request.data['password'])
        try:
            validate_password(request.data['password'], user)
            token = user.profile.token
        except ValidationError as e:
            error = list(e)
            user.delete()
    except:
        error = 'Username already exists.'
    return {'token': token, 'error': error}

@require_POST
def login(request):
    token = None
    error = ''
    user = authenticate(username=request.data['username'], password=request.data['password'])
    if user is not None:
        auth_login(request, user)
        if user.profile.expired:
            user.profile.new_token()
        token = user.profile.token
    else:
        error = 'Invalid credentials.'
    return {'token': token, 'error': error}

@require_POST
@auth
def logout(request):
    request.profile.expired = True
    request.profile.save()

@require_GET
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

@require_GET
@auth
def personality(request):
    return {
        "fire": {"value": 0.678, "positive": True},
        "water": {"value": 0.678, "positive": False},
        "earth": {"value": 0.678, "positive": True},
        "air": {"value": 0.678, "positive": False},
        "space": {"value": 0.678, "positive": True},
    } # dummy data

@require_http_methods(["GET", "POST"])
@auth
def personality_update(request):
    if request.method == "GET":
        try:
            questionnaire = PersonalityQuestionnaire.objects.get(user=request.profile.user, submitted=False)
        except PersonalityQuestionnaire.DoesNotExist:
            questionnaire = PersonalityQuestionnaire.objects.create(user=request.profile.user)
        return {
            "id": questionnaire.id,
            "questions": ["How extrovert are you?", "How depressed are you?"], # dummy data
        }
    else:
        try:
            questionnaire = PersonalityQuestionnaire.objects.get(pk=request.data['id'])
            if questionnaire.user != request.profile.user:
                return {'error': 'Invalid questionnaire.'}
            if questionnaire.submitted:
                return {'error': 'Questionnaire already answered.'}
            questionnaire.submitted = True
            questionnaire.submit_time = timezone.localtime()
            questionnaire.save()
            # update user personality based on answers
        except PersonalityQuestionnaire.DoesNotExist:
            return {'error': 'Questionnaire not found.', 'code': 404}

@require_GET
@auth
def me_interests(request):
    return [{
        "id": user_interest.interest.id,
        "name": user_interest.interest.name,
        "amount": user_interest.amount,
        "answers": [{"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)]
    } for user_interest in UserInterest.objects.filter(user=request.profile.user)]

@require_GET
@auth
def me_interest(request, pk):
    try:
        user_interest = UserInterest.objects.get(user=request.profile.user, interest=pk)
        return {
            "name": user_interest.interest.name,
            "amount": user_interest.amount,
            "answers": [{"question": answer.question.text, "answer": answer.text} for answer in Answer.objects.filter(user_interest=user_interest)]
        }
    except UserInterest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}

@require_POST
@auth
def update_interests(request):
    user_interests = UserInterest.objects.filter(user=request.profile.user, interest__in=request.data['interests'])
    for user_interest in user_interests:
        index = request.data['interests'].index(user_interest.interest.pk)
        if amount := request.data['amounts'][index]:
            user_interest.amount = request.data['amounts'][index]
            user_interest.save()
            request.data['amounts'][index] = 0
        else:
            user_interest.delete()
    try:
        for index, amount in enumerate(request.data['amounts']):
            if amount != 0:
                interest = Interest.objects.get(pk=request.data['interests'][index])
                user_interest = UserInterest.objects.create(user=request.profile.user, interest=interest, amount=amount)
                user_interest.save()
    except Interest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}

@require_POST
@auth
def update_interest(request, pk):
    try:
        user_interest = UserInterest.objects.get(user=request.profile.user, interest=pk)
        question = Question.objects.get(pk=request.data['question'])
        text = request.data['answer']
        try:
            answer = Answer.objects.get(user_interest=user_interest, question=question)
            answer.text = text
        except Answer.DoesNotExist:
            answer = Answer.objects.create(user_interest=user_interest, question=question, text=text)
        answer.save()
    except UserInterest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}
    except Question.DoesNotExist:
        return {'error': 'Question not found.', 'code': 404}

@require_GET
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

@require_POST
@auth
def me_avatar_update(request):
    try:
        avatar = Avatar.objects.get(pk=request.data['id'])
        request.profile.avatar = avatar
        request.profile.save()
    except Avatar.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
@auth
def interests(request):
    return [{"id": interest.id, "name": interest.name} for interest in Interest.objects.all()]

@require_GET
@auth
def interest(request, pk):
    try:
        interest = Interest.objects.get(pk=pk)
        return {"name": interest.name, "questions": [{"id": question.id, "text": question.text} for question in Question.objects.filter(interest=interest)]}
    except Interest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}

@require_GET
@auth
def base_avatars(request):
    return [{"id": base.id, "name": base.name, "url": base.url} for base in AvatarBase.objects.all()]

@require_GET
@auth
def avatars(request, pk):
    try:
        base = AvatarBase.objects.get(pk=pk)
        return [{"id": avatar.id, "mood": avatar.mood.name, "url": avatar.url} for avatar in Avatar.objects.filter(base=base)]
    except AvatarBase.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
@auth
def find(request):
    return {
        "users": [{
            "id": access.id,
            "avatar": access.other.avatar.url,
            "mood": access.other.avatar.mood.name,
            "personality": {
                "fire": {"value": 0.678, "positive": True},
                "water": {"value": 0.678, "positive": False},
            }, # dummy data
        } for access in Access.objects.filter(me=request.profile)],
        "views-remaining": MAX_PROFILE_VIEWS - Access.objects.filter(me=request.profile).filter(viewed=True).count(),
    }

@require_POST
@auth
def view(request):
    try:
        access = Access.objects.get(pk=request.data['id'])
        if access.me == request.profile:
            if not access.viewed:
                if Access.objects.filter(me=request.profile).filter(viewed=True).count() >= MAX_PROFILE_VIEWS:
                    return {'error': 'Maximum profile views reached.'}
                access.viewed = True
                access.view_time = timezone.localtime()
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
            return {'error': 'User not found.', 'code': 404}
    except Access.DoesNotExist:
        return {'error': 'User not found.', 'code': 404}

@require_POST
@auth
def request(request):
    try:
        access = Access.objects.get(pk=request.data['id'])
        if access.me == request.profile and access.viewed:
            if access.requested:
                return {'error': 'Already requested.'}
            access.requested = True
            access.request_time = timezone.localtime()
            access.save()
        else:
            return {'error': 'User not found.', 'code': 404}
    except Access.DoesNotExist:
        return {'error': 'User not found.', 'code': 404}

@require_GET
@auth
def requests(request):
    return [{
        "id": access.id,
        "avatar": access.me.avatar.url,
    } for access in Access.objects.filter(other=request.profile).filter(requested=True).filter(connected=False)]

@require_POST
@auth
def accept(request):
    try:
        access = Access.objects.get(pk=request.data['id'])
        if access.other == request.profile and access.requested:
            if access.connected:
                return {'error': 'Request already accepted.'}
            access.connected = True
            access.connect_time = timezone.localtime()
            access.save()
            connect = Connect.objects.create(user1=access.me, user2=access.other)
            connect.save()
        else:
            return {'error': 'Request not found.', 'code': 404}
    except Access.DoesNotExist:
        return {'error': 'Request not found.', 'code': 404}

@require_GET
@auth
def found(request):
    connects = [(connect.user2, connect.id, connect.retained()) for connect in Connect.objects.filter(user1=request.profile)]
    connects += [(connect.user1, connect.id, connect.retained()) for connect in Connect.objects.filter(user2=request.profile)]
    return [{
        "id": id,
        "nick": profile.user.username,
        "avatar": profile.avatar.url,
        "retained": retained
    } for profile, id, retained in connects]

@require_POST
@auth
def retain(request):
    try:
        connect = Connect.objects.get(pk=request.data['id'])
        if connect.user1 == request.profile:
            if connect.retained1:
                return {'error': 'User already retained.'}
            connect.retained1 = True
            connect.retain1_time = timezone.localtime()
            if connect.retained2:
                connect.retain_time = timezone.localtime()
            connect.save()
        elif connect.user2 == request.profile:
            if connect.retained2:
                return {'error': 'User already retained.'}
            connect.retained2 = True
            connect.retain2_time = timezone.localtime()
            if connect.retained1:
                connect.retain_time = timezone.localtime()
            connect.save()
        else:
            return {'error': 'Connect not found.', 'code': 404}
    except Connect.DoesNotExist:
        return {'error': 'Connect not found.', 'code': 404}
