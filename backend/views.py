from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils import timezone

from .decorators import auth_exempt
from .models import *
from .firebase import get_last_message, get_unread_num

from algo.parameters import *


MAX_PROFILE_VIEWS = 0
QUESTION_FACETS = {
    "Make friends easily.": (Trait.E, 1),
    "Spend time reflecting on things.": (Trait.O, 1),
    "Feel comfortable with myself.": (Trait.N, -3),
    "Make people feel welcome.": (Trait.A, 3),
    "Remain calm under pressure.": (Trait.N, -6),
    "Am willing to try anything once.": (Trait.E, 5),
    "Believe that there is no absolute right and wrong.": (Trait.O, 6),
    "Need a push to get started.": (Trait.C, -5),
    "Do just enough work to get by.": (Trait.C, -4),
    "Value cooperation over competition.": (Trait.A, 6),
}

@require_GET
@auth_exempt
def index(request):
    return {"message": "API root node"}

@require_POST
@auth_exempt
def register(request):
    token = None
    error = ''
    try:
        user = User.objects.create_user(request.data['username'], password=request.data['password'])
        try:
            validate_password(request.data['password'], user)
            auth_login(request, user)
            token = user.profile.token
        except ValidationError as e:
            error = '\n'.join(list(e))
            user.delete()
    except:
        error = 'Username already exists.'
    return {'token': token, 'error': error}

@require_POST
@auth_exempt
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
def logout(request):
    request.profile.expired = True
    request.profile.save()

@require_GET
def me(request):
    return request.profile.get_info()

@require_GET
def personality(request):
    return request.profile.traits

@require_http_methods(["GET", "POST"])
@auth_exempt
def personality_update(request):
    if request.method == "GET":
        all = PersonalityQuestionnaire.objects.all()
        initial = all.filter(initial=True)
        return {
            'all': [obj.url for obj in all],
            'initial': [obj.url for obj in initial],
        }
    else:
        try:
            nick = request.data.pop('FindMe Nick')
            profile = Profile.objects.get(user__username=nick)
        except Profile.DoesNotExist:
            return {'error': 'Nick not found.'}

        facets = [0 for _ in range(NUM_FACETS)]
        for question in request.data:
            if question[:8] != 'tripetto':
                trait, facet = QUESTION_FACETS[question]
                value = (int(request.data[question]) / 5) * 0.998 + 0.001
                if facet < 0:
                    value = 1 - value
                facets[trait.value * FACETS_PER_TRAIT + abs(facet) - 1] = value

        if profile.last_questionnaire_time is None:
            profile.save_facets(facets)
        else:
            days = (timezone.now() - profile.last_questionnaire_time).days
            if days < 1:
                weight = 0.15
            elif days < 7:
                weight = 0.3
            elif days < 14:
                weight = 0.4
            elif days < 30:
                weight = 0.5
            elif days < 60:
                weight = 0.6
            else:
                weight = 0.75

            prev_facets = profile.facets
            for index, value in enumerate(facets):
                if value != 0:
                    if prev_facets[index] == 0:
                        prev_facets[index] = value
                    else:
                        prev_facets[index] = value * weight + prev_facets[index] * (1 - weight)
            profile.save_facets(prev_facets)

@require_GET
def me_interests(request):
    return request.profile.get_all_interests()

@require_GET
def me_interest(request, pk):
    return request.profile.get_interest(pk)

@require_POST
def update_interests(request):
    for data in request.data:
        try:
            interest = Interest.objects.get(pk=data['interest'])
            try:
                user_interest = UserInterest.objects.get(user=request.profile, interest=interest)
                user_interest.amount = data['amount']
            except UserInterest.DoesNotExist:
                user_interest = UserInterest.objects.create(user=request.profile, interest=interest, amount=data['amount']) if data['amount'] else None
        except Interest.DoesNotExist:
            return {'error': 'Interest not found.', 'code': 404}

        if user_interest:
            user_interest.save()

@require_POST
def update_interest(request, pk):
    try:
        user_interest = UserInterest.objects.get(user=request.profile, interest=pk)
        for data in request.data:
            question = Question.objects.get(pk=data['question'], interest=pk)
            text = data['answer']
            try:
                answer = Answer.objects.get(user_interest=user_interest, question=question)
                if text:
                    answer.text = text
                else:
                    answer.delete()
                    answer = None
            except Answer.DoesNotExist:
                answer = Answer.objects.create(user_interest=user_interest, question=question, text=text) if text else None
            if answer:
                answer.save()
    except UserInterest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}
    except Question.DoesNotExist:
        return {'error': 'Question not found.', 'code': 404}

@require_GET
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
def me_avatar_update(request):
    try:
        avatar = Avatar.objects.get(pk=request.data['id'])
        request.profile.avatar = avatar
        request.profile.save()
    except Avatar.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
def interests(request):
    user_interests = UserInterest.objects.filter(user=request.profile)

    def find_amount(interest):
        try:
            interest = user_interests.get(interest=interest)
            return interest.amount
        except UserInterest.DoesNotExist:
            return 0

    return [{
        "id": interest.id,
        "name": interest.name,
        "amount": find_amount(interest),
        "questions": [{
            "id": question.id,
            "question": question.text,
            "answer": ""
        } for question in Question.objects.filter(interest=interest)],
    } for interest in Interest.objects.all()]

@require_GET
def interest(request, pk):
    try:
        interest = Interest.objects.get(pk=pk)
        return {"name": interest.name, "questions": [{"id": question.id, "text": question.text} for question in Question.objects.filter(interest=interest)]}
    except Interest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}

@require_GET
def base_avatars(request):
    return [{"id": base.id, "name": base.name, "url": base.url} for base in AvatarBase.objects.all()]

@require_GET
def avatars(request, pk):
    try:
        base = AvatarBase.objects.get(pk=pk)
        return [{"id": avatar.id, "mood": avatar.mood.name, "url": avatar.url} for avatar in Avatar.objects.filter(base=base)]
    except AvatarBase.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
def find(request):
    return {
        "users": [{**access.other.get_basic_info(), **{"id": access.id}} for access in Access.objects.filter(active=True).filter(me=request.profile).filter(connected=False)],
        "views-remaining": MAX_PROFILE_VIEWS - Access.objects.filter(active=True).filter(me=request.profile).filter(viewed=True).count(),
    }

@require_GET
def find_view(request, pk):
    try:
        access = Access.objects.get(pk=pk)
        if access.active and access.me == request.profile:
            if not access.viewed:
                if MAX_PROFILE_VIEWS and Access.objects.filter(active=True).filter(me=request.profile).filter(viewed=True).count() >= MAX_PROFILE_VIEWS:
                    return {'error': 'Maximum profile views reached.'}
                access.viewed = True
                access.save()
            return access.other.get_info()
    except Access.DoesNotExist:
        pass
    return {'error': 'User not found.', 'code': 404}

@require_POST
def request(request):
    try:
        access = Access.objects.get(pk=request.data['id'])
        if access.active and access.me == request.profile and access.viewed:
            if access.requested:
                return {'error': 'Already requested.'}
            access.requested = True
            access.save()
            return
    except Access.DoesNotExist:
        pass
    return {'error': 'User not found.', 'code': 404}

@require_GET
def views(request):
    return [{**access.me.get_info(interest_questions=False), **{"id": access.id}} for access in Access.objects.filter(active=True).filter(other=request.profile).filter(viewed=True).filter(requested=False)]

@require_GET
def view_view(request, pk):
    try:
        access = Access.objects.get(pk=pk)
        if access.active and access.viewed and not access.requested and access.other == request.profile:
            return access.me.get_info()
    except Access.DoesNotExist:
        pass
    return {'error': 'User not found.', 'code': 404}

@require_GET
def requests(request):
    return [{**access.me.get_basic_info(), **{"id": access.id}} for access in Access.objects.filter(active=True).filter(other=request.profile).filter(requested=True).filter(connected=False)]

@require_GET
def request_view(request, pk):
    try:
        access = Access.objects.get(pk=pk)
        if access.active and access.requested and not access.connected and access.other == request.profile:
            return access.me.get_info()
    except Access.DoesNotExist:
        pass
    return {'error': 'User not found.', 'code': 404}

@require_POST
def accept(request):
    try:
        access = Access.objects.get(pk=request.data['id'])
        if access.active and access.other == request.profile and access.requested:
            if access.connected:
                return {'error': 'Request already accepted.'}
            access.connected = True
            access.save()
            return
    except Access.DoesNotExist:
        pass
    return {'error': 'Request not found.', 'code': 404}

@require_GET
def found(request):
    connects = [(connect.id, connect.chat_id, 1, get_last_message(connect.chat_id), get_unread_num(connect.chat_id, 1, connect.last_read_time1), connect.retained1, connect.user2, connect.retained()) for connect in Connect.objects.filter(active=True).filter(user1=request.profile)]
    connects += [(connect.id, connect.chat_id, 2, get_last_message(connect.chat_id), get_unread_num(connect.chat_id, 1, connect.last_read_time1), connect.retained2, connect.user1, connect.retained()) for connect in Connect.objects.filter(active=True).filter(user2=request.profile)]
    return [{**profile.get_basic_info(), **{
        "id": id,
        "me": me,
        "chat_id": chat_id,
        "last_message": last_message,
        "unread_num": unread_num,
        "retain_request_sent": retain_request,
        "retained": retained,
    }} for id, chat_id, me, last_message, unread_num, retain_request, profile, retained in connects]

@require_POST
def found_read(request):
    try:
        connect = Connect.objects.get(active=True, pk=request.data['id'])
        if connect.user1 == request.profile:
            connect.last_read_time1 = timezone.now()
            connect.save()
            return
        if connect.user2 == request.profile:
            connect.last_read_time2 = timezone.now()
            connect.save()
            return
    except Connect.DoesNotExist:
        pass
    return {'error': 'Connect not found.', 'code': 404}

@require_GET
def found_view(request, pk):
    try:
        connect = Connect.objects.get(pk=pk)
        if connect.active:
            if connect.user1 == request.profile:
                return connect.user2.get_info()
            if connect.user2 == request.profile:
                return connect.user1.get_info()
    except Connect.DoesNotExist:
        pass
    return {'error': 'User not found.', 'code': 404}

@require_POST
def retain(request):
    try:
        connect = Connect.objects.get(active=True, pk=request.data['id'])
        if connect.retained():
            return {'error': 'User already retained.'}
        if connect.user1 == request.profile:
            if connect.retained1:
                return {'error': 'Retain request already sent.'}
            connect.retained1 = True
            connect.save()
            return
        if connect.user2 == request.profile:
            if connect.retained2:
                return {'error': 'Retain request already sent.'}
            connect.retained2 = True
            connect.save()
            return
    except Connect.DoesNotExist:
        pass
    return {'error': 'Connect not found.', 'code': 404}
