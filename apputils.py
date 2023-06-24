from flask import request

def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    form = str(hash(frozenset(request.form.items())))
    return (path + args + form).encode('utf-8')



