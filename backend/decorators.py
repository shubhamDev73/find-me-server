from functools import wraps

def auth_exempt(function):

    def wrap(*args, **kwargs):
        return function(*args, **kwargs)
    wrap.auth_exempt = True
    return wraps(function)(wrap)
