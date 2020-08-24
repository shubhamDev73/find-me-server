class PostJsonMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        import json

        if request.method == "POST":
            if string := request.body.decode("utf-8"):
                try:
                    request.data = json.loads(string)
                except:
                    pass
            else:
                request.data = {}

        return self.get_response(request)

class AuthTokenMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        from django.http import HttpResponse, JsonResponse
        from .models import Profile

        request.profile = None
        code = 200
        try:
            splits = request.META['HTTP_AUTHORIZATION'].split("Bearer ")
            if len(splits) == 2 and splits[0] == "":
                token = splits[1]
                try:
                    profile = Profile.objects.get(token=token)
                    if profile.expired:
                        request.auth_error = 'Auth token expired.'
                        code = 401
                    else:
                        request.profile = profile
                except Profile.DoesNotExist:
                    request.auth_error = 'Invalid auth token.'
                    code = 403
            else:
                request.auth_error = 'Invalid auth header.'
                code = 400
        except:
            request.auth_error = 'Missing authorization.'
            code = 403

        data = self.get_response(request)
        if isinstance(data, HttpResponse):
            return data

        response = {}
        if type(data) is dict and 'error' in data:
            response['error'] = data.pop('error')
            if 'code' in data:
                code = data.pop('code')

        if 'error' not in response or response['error'] == '':
            response = data

        return JsonResponse(response, safe=False, status=code)
