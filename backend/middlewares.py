import json
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse

from .models import Profile


class PostJsonMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST":
            try:
                request.data = json.loads(request.body.decode("utf-8"))
            except:
                request.data = {}
        return self.get_response(request)

class AuthTokenMiddleware(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):

        response = {'error': ''}
        code = 200

        if request.resolver_match.app_name == 'api' and not getattr(view_func, 'auth_exempt', False):
            try:
                splits = request.META['HTTP_AUTHORIZATION'].split("Bearer ")
                if len(splits) == 2 and splits[0] == "":
                    token = splits[1]
                    try:
                        profile = Profile.objects.get(token=token)
                        if profile.expired:
                            response['error'] = 'Auth token expired.'
                            code = 401
                        else:
                            request.profile = profile
                    except Profile.DoesNotExist:
                        response['error'] = 'Invalid auth token.'
                        code = 403
                else:
                    response['error'] = 'Invalid auth header.'
                    code = 400
            except:
                response['error'] = 'Missing authorization.'
                code = 403

        if code == 200:
            data = view_func(request, *view_args, **view_kwargs)
            if isinstance(data, HttpResponse) or isinstance(data, StreamingHttpResponse):
                return data

            request.session.pop('_auth_user_id', None)
            request.session.pop('_auth_user_backend', None)
            request.session.pop('_auth_user_hash', None)

            if type(data) is dict and 'error' in data:
                response['error'] = data.pop('error')
                if 'code' in data:
                    code = data.pop('code')

            if response['error'] == '':
                response = data

        return JsonResponse(response, safe=False, status=code)
