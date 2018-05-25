def traceme(modulename):
    def _traceme(fn):
        def _fn(*args, **kwargs):
            print("    STUB: %s.%s(args=%r kwargs=%r)" % (modulename, fn.__name__, args, kwargs))
            return fn(*args, **kwargs)
        return _fn
    return _traceme

