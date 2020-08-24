class PostJsonMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        import json

        if request.method == "POST":
            request.data = json.loads(request.body.decode("utf-8"))

        return self.get_response(request)

class AuthTokenMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        from django.http import HttpResponse, JsonResponse
        from .models import Profile

        request.profile = None
        try:
            splits = request.META['HTTP_AUTHORIZATION'].split("Bearer ")
            if len(splits) == 2 and splits[0] == "":
                token = splits[1]
                try:
                    profile = Profile.objects.get(token=token)
                    if profile.expired:
                        request.auth_error = 'token expired'
                    else:
                        request.profile = profile
                except Profile.DoesNotExist:
                    request.auth_error = 'invalid token'
            else:
                request.auth_error = 'invalid header'
        except:
            request.auth_error = 'invalid authorization'

        data = self.get_response(request)
        if isinstance(data, HttpResponse):
            return data

        response = {}
        if type(data) is dict and 'error' in data:
            response['error'] = data['error']
            data.pop('error')

        if 'error' not in response or response['error'] == '':
            response = data

        return JsonResponse(response, safe=False)
