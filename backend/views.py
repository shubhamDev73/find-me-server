import json

from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils import timezone
from django.core.mail import send_mail

from .decorators import auth_exempt
from .models import *
from . import firebase

from algo.parameters import *


MAX_PROFILE_VIEWS = 0
MOOD_CHANGE_TIME = 60 * 60 * 4 # in seconds
QUESTION_FACETS = {
    "Do you find it easy to meet new people and make friends?": (Trait.E, 1),
    "Do you pause and reflect upon things?": (Trait.O, 1),
    "Do you feel uncomfortable with yourself?": (Trait.N, 3),
    "Do you make people feel welcome?": (Trait.A, 3),
    "Do you have a tendency to remain calm under pressure?": (Trait.N, -6),
    "Are you willing to try anything once?": (Trait.E, 5),
    "Do you feel that there is no absolute right and wrong?": (Trait.O, 6),
    "Is there a push required for you to get started?": (Trait.C, -5),
    "Do you believe in doing just enough work to get by?": (Trait.C, -4),
    "Do you value competition over cooperation in a real life scenario?": (Trait.A, -6)
}
OPTION_VALUES = {
    "never": 1,
    "rarely": 2,
    "sometimes": 3,
    "often": 4,
    "regularly": 5,
}

def get_user(request):
    user = None
    try:
        user = User.objects.get(username=request.data['username'])
    except:
        try:
            user = User.objects.get(email=request.data['username'])
        except:
            try:
                user = User.objects.get(phone=request.data['username'])
            except:
                try:
                    user = User.objects.get(email=request.data['email'])
                except:
                    try:
                        user = User.objects.get(phone=request.data['phone'])
                    except:
                        user = None
    return user

@require_GET
@auth_exempt
def index(request):
    return {"message": "API root node"}

@require_POST
@auth_exempt
def register(request):
    token = None
    onboarded = False
    error = ''

    user = get_user(request)
    if user is not None:
        error = 'User already exists.'
    else:
        user = User.objects.create_user(request.data['username'], password=request.data['password'])
        user.fill_details(email=request.data.get('email'), phone=request.data.get('phone'))
        try:
            validate_password(request.data['password'], user)
            auth_login(request, user)
            user.otp = ''
            user.verified = False
            user.save()
            token = user.token
            onboarded = user.profile.onboarded
        except ValidationError as e:
            error = '\n'.join(list(e))
            user.delete()

    return {'token': token, 'onboarded': onboarded, 'error': error}

@require_POST
@auth_exempt
def login(request):
    token = None
    onboarded = False
    error = ''

    user = get_user(request)
    if user is not None:
        user = authenticate(username=user.username, password=request.data['password'])
        if user is not None:
            auth_login(request, user)
            user.otp = ''
            user.verified = False
            user.save()
            if user.expired:
                user.new_token()
            token = user.token
            onboarded = user.profile.onboarded
        else:
            error = 'Invalid credentials.'
    else:
        error = 'Invalid credentials.'

    return {'token': token, 'onboarded': onboarded, 'error': error}

@require_POST
@auth_exempt
def login_external(request):
    token = None
    onboarded = False
    error = ''

    email = request.data['email']
    external_id = request.data['external_id']
    key = list(external_id.keys())[0]

    try:
        user = User.objects.get(email=email)
        user_ids = {} if user.external_ids == '' else json.loads(user.external_ids)

        id = user_ids.get(key)
        if id is None:
            user_ids[key] = external_id[key]
            user.external_ids = json.dumps(user_ids)
            auth_login(request, user)
            user.otp = ''
            user.verified = False
            user.save()
            if user.expired:
                user.new_token()
            token = user.token
            onboarded = user.profile.onboarded
        elif id == external_id[key]:
            if user.expired:
                user.new_token()
            token = user.token
            onboarded = user.profile.onboarded
        else:
            error = 'Invalid credentials.'
    except User.DoesNotExist:
        user = User.objects.create_user(email, email=email, external_ids=json.dumps(external_id))
        user.set_unusable_password()
        auth_login(request, user)
        user.otp = ''
        user.verified = False
        user.save()
        token = user.token
        onboarded = user.profile.onboarded
    return {'token': token, 'onboarded': onboarded, 'error': error}

@require_POST
def fill_details(request):
    user = get_user(request)
    if user is None or user == request.profile.user:
        if 'password' in request.data:
            request.profile.user.set_password(request.data['password'])
            request.profile.user.save()
        request.profile.user.fill_details(username=request.data.get('username'), email=request.data.get('email'), phone=request.data.get('phone'))
    else:
        return {'error': 'User already exists.'}

@require_POST
def logout(request):
    request.profile.user.expired = True
    request.profile.user.fcm_token = ''
    request.profile.user.save()

@require_POST
@auth_exempt
def otp_send(request):
    user = get_user(request)

    if user is not None:

        import string
        import secrets
        otp = ''.join(secrets.choice(string.digits) for _ in range(4))

        user.otp = make_password(otp)
        user.verified = False
        user.save()

        if user.email is not None:
            send_mail(
                'OTP for find.me password reset',
                f'{otp} is the otp for your password reset request on find.me',
                'shubham0209@gmail.com',
                [user.email],
                fail_silently=False,
            )

    return {'message': 'OTP sent on registered email.'}

@require_POST
@auth_exempt
def otp_check(request):
    user = get_user(request)

    if user is not None:
        if check_password(request.data['otp'], user.otp):
            user.otp = ''
            user.verified = True
            user.save()
            return {'message': 'Correct OTP entered.'}
        else:
            return {'error': 'Invalid OTP entered.'}

@require_POST
@auth_exempt
def password_reset(request):
    user = get_user(request)
    if user is not None and user.verified:
        user.verified = False
        user.set_password(request.data['password'])
        user.save()
        return {'message': 'Password reset successfully.'}

    return {'error': 'Password reset failed.'}

@require_GET
def me(request):
    return request.profile.get_info(empty_questions=True)

@require_GET
def me_personality(request):
    return request.profile.traits

@require_http_methods(["GET", "POST"])
@auth_exempt
def me_personality_update(request):
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

        facets = [None for _ in range(NUM_FACETS)]
        for question in request.data:
            trait, facet = QUESTION_FACETS.get(question, (None, None))
            if trait is None:
                continue
            value = ((OPTION_VALUES[request.data[question]] - 1)/ 4) * 0.998 + 0.001
            if facet < 0:
                value = 1 - value
            facets[trait.value * FACETS_PER_TRAIT + abs(facet) - 1] = value

        if profile.last_questionnaire_time is None:
            for trait in range(NUM_TRAITS):
                absent = []
                avg = 0
                for i in range(FACETS_PER_TRAIT):
                    facet = facets[trait * FACETS_PER_TRAIT + i]
                    if facet is None:
                        absent.append(i)
                    else:
                        avg += facet
                avg /= FACETS_PER_TRAIT - len(absent)
                for i in absent:
                    facets[trait * FACETS_PER_TRAIT + i] = avg

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
                if value is not None:
                    if prev_facets[index] == 0:
                        prev_facets[index] = value
                    else:
                        prev_facets[index] = value * weight + prev_facets[index] * (1 - weight)
            profile.save_facets(prev_facets)
        firebase.send_notification(profile, {'title': 'Personality updated!', 'body': 'Your personality has been updated according to the questions you answered!'}, type='Personality')

@require_GET
def me_interests(request):
    return request.profile.get_all_interests()

@require_GET
def me_interest(request, pk):
    return request.profile.get_interest(pk)

@require_POST
def update_interests(request):
    try:
        interest = Interest.objects.get(pk=request.data['interest'])
        try:
            user_interest = UserInterest.objects.get(user=request.profile, interest=interest)
            user_interest.amount = request.data['amount']
        except UserInterest.DoesNotExist:
            user_interest = UserInterest.objects.create(user=request.profile, interest=interest, amount=request.data['amount']) if request.data['amount'] else None
    except Interest.DoesNotExist:
        return {'error': 'Interest not found.', 'code': 404}

    if user_interest:
        user_interest.save()

@require_POST
def update_interest(request, pk):
    try:
        user_interest = UserInterest.objects.get(user=request.profile, interest=pk)
        question = Question.objects.get(pk=request.data['question'], interest=pk)
        text = request.data['answer']
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
        if avatar == request.profile.avatar:
            return

        last_timeline = AvatarTimeline.objects.filter(user=request.profile).order_by('-timestamp')
        if len(last_timeline):
            last_timeline = last_timeline[0]
        else:
            last_timeline = None

        if last_timeline and (timezone.now() - last_timeline.timestamp).total_seconds() < MOOD_CHANGE_TIME:
            timeline = last_timeline
            timeline.avatar = avatar
        else:
            timeline = AvatarTimeline.objects.create(user=request.profile, avatar=avatar)
        timeline.save()

        request.profile.avatar = avatar
        request.profile.save()
    except Avatar.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
def interests(request):
    return [{
        "id": interest.id,
        "name": interest.name,
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
    return [{
        "id": base.id,
        "name": base.name,
        "url": base.url,
        "avatars": [{"id": avatar.id, "mood": avatar.mood.name, "url": avatar.url} for avatar in Avatar.objects.filter(base=base).order_by('mood__name')]
    } for base in AvatarBase.objects.all()]

@require_GET
def avatars(request, pk):
    try:
        base = AvatarBase.objects.get(pk=pk)
        return [{"id": avatar.id, "mood": avatar.mood.name, "url": avatar.url} for avatar in Avatar.objects.filter(base=base)]
    except AvatarBase.DoesNotExist:
        return {'error': 'Avatar not found.', 'code': 404}

@require_GET
def moods(request):
    return [{"id": mood.id, "name": mood.name, "url": mood.url} for mood in Mood.objects.all()]

@require_GET
def personality(request):
    all_questionnaires = PersonalityQuestionnaire.objects.all()
    initial_questionnaires = all_questionnaires.filter(initial=True)

    return {
        "trait": {
            personality.display_name: {
                "description": personality.description,
                "url": personality.get_urls(),
                "adjectives": [{"id": adjective.id, "name": adjective.name, "description": adjective.description, "pool": adjective.pool} for adjective in Adjective.objects.filter(trait=personality.trait)],
            } for personality in Personality.objects.all()
        },
        "questionnaire": {
            "all": [obj.url for obj in all_questionnaires],
            "initial": [obj.url for obj in initial_questionnaires],
        },
    }

@require_GET
def find(request):
    return {
        "users": [{**access.other.get_basic_info(), **{"id": access.id, "timestamp": access.create_time}} for access in Access.objects.filter(active=True).filter(me=request.profile).filter(connected=False)],
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
    return [{**access.me.get_basic_info(), **{"id": access.id, "timestamp": access.view_time}} for access in Access.objects.filter(active=True).filter(other=request.profile).filter(viewed=True).filter(requested=False)]

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
    return [{**access.me.get_basic_info(), **{"id": access.id, "timestamp": access.request_time}} for access in Access.objects.filter(active=True).filter(other=request.profile).filter(requested=True).filter(connected=False)]

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
    connects = [(connect, 1) for connect in Connect.objects.filter(active=True).filter(user1=request.profile)]
    connects += [(connect, 2) for connect in Connect.objects.filter(active=True).filter(user2=request.profile)]
    return [{**(connect.user2 if me == 1 else connect.user1).get_basic_info(), **{
        "id": connect.id,
        "timestamp": connect.create_time,
        "me": me,
        "chat_id": connect.chat_id,
        "last_message": firebase.get_last_message(connect.chat_id),
        "unread_num": firebase.get_unread_num(connect.chat_id, me, connect.last_read_time1 if me == 1 else connect.last_read_time2),
        "retain_request_sent": connect.retained1 if me == 1 else connect.retained2,
        "retained": connect.retained(),
    }} for connect, me in connects]

@require_POST
def found_read(request):
    try:
        connect = Connect.objects.get(active=True, pk=request.data['id'])
        time = timezone.now()
        if connect.user1 == request.profile and time > connect.last_read_time1:
            connect.last_read_time1 = time
            connect.save()
            return
        if connect.user2 == request.profile and time > connect.last_read_time2:
            connect.last_read_time2 = time
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
                return connect.user2.get_info(empty_questions=True)
            if connect.user2 == request.profile:
                return connect.user1.get_info(empty_questions=True)
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

@require_POST
def notification_token(request):
    if token := request.data.get('fcm_token'):
        request.profile.user.fcm_token = token
        request.profile.user.save()
    else:
        return {'error': 'No fcm token specified.'}

@require_POST
def notification_send(request):
    if (type := request.data.get('type')) and (id := request.data.get('id')):
        if type == 'chat':
            try:
                connect = Connect.objects.get(active=True, id=id)
            except Connect.DoesNotExist:
                return {'error': 'Connect not found.', 'code': 404}

            profile = None
            if connect.user1 == request.profile:
                profile = connect.user2
            if connect.user2 == request.profile:
                profile = connect.user1

            if profile is None:
                return {'error': 'Connect not found.', 'code': 404}

            firebase.send_notification(profile, {'title': request.profile.user.username, 'body': request.data.get('message', '')}, type='Chat', id=str(id), display='false')
        else:
            return {'error': 'Invalid type.', 'code': 400}
    else:
        return {'error': 'Some required parameters missing.', 'code': 400}
