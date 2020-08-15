def auth(function):

    def wrap(request, *args, **kwargs):
        if request.profile is not None:
            if response := function(request, *args, **kwargs):
                return response
            return {}
        return {'error': request.auth_error}

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
