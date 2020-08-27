import json
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse

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

class AuthTokenMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.profile = None
        request.auth_error_status_code = 200
        try:
            splits = request.META['HTTP_AUTHORIZATION'].split("Bearer ")
            if len(splits) == 2 and splits[0] == "":
                token = splits[1]
                try:
                    profile = Profile.objects.get(token=token)
                    if profile.expired:
                        request.auth_error = 'Auth token expired.'
                        request.auth_error_status_code = 401
                    else:
                        request.profile = profile
                except Profile.DoesNotExist:
                    request.auth_error = 'Invalid auth token.'
                    request.auth_error_status_code = 403
            else:
                request.auth_error = 'Invalid auth header.'
                request.auth_error_status_code = 400
        except:
            request.auth_error = 'Missing authorization.'
            request.auth_error_status_code = 403

        data = self.get_response(request)
        if isinstance(data, HttpResponse) or isinstance(data, StreamingHttpResponse):
            return data

        request.session.pop('_auth_user_id', None)
        request.session.pop('_auth_user_backend', None)
        request.session.pop('_auth_user_hash', None)

        response = {}
        code = 200

        if type(data) is dict and 'error' in data:
            response['error'] = data.pop('error')
            if 'code' in data:
                code = data.pop('code')

        if 'error' not in response or response['error'] == '':
            response = data

        return JsonResponse(response, safe=False, status=code)
