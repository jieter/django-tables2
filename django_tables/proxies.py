from django.utils.functional import Promise


class AbstractProxy(object):
    """Delegates all operations (except ``.__subject__``) to another object"""
    __slots__ = ()

    #def __call__(self, *args, **kw):
    #    return self.__subject__(*args, **kw)

    def __getattribute__(self, attr, oga=object.__getattribute__):
        subject = oga(self,'__subject__')
        if attr=='__subject__':
            return subject
        return getattr(subject,attr)

    def __setattr__(self, attr, val, osa=object.__setattr__):
        if attr == '__subject__':
            osa(self, attr, val)
        else:
            setattr(self.__subject__, attr, val)

    def __delattr__(self, attr, oda=object.__delattr__):
        if attr=='__subject__':
            oda(self,attr)
        else:
            delattr(self.__subject__, attr)

    def __nonzero__(self):
        return bool(self.__subject__)

    def __getitem__(self, arg):
        return self.__subject__[arg]

    def __setitem__(self, arg, val):
        self.__subject__[arg] = val

    def __delitem__(self, arg):
        del self.__subject__[arg]

    def __getslice__(self, i, j):
        return self.__subject__[i:j]


    def __setslice__(self, i, j, val):
        self.__subject__[i:j] = val

    def __delslice__(self, i, j):
        del self.__subject__[i:j]

    def __contains__(self, ob):
        return ob in self.__subject__

    for name in 'repr str hash len abs complex int long float iter oct hex'.split():
        exec "def __%s__(self): return %s(self.__subject__)" % (name, name)

    for name in 'cmp', 'coerce', 'divmod':
        exec "def __%s__(self,ob): return %s(self.__subject__,ob)" % (name, name)

    for name, op in [
        ('lt','<'), ('gt','>'), ('le','<='), ('ge','>='),
        ('eq','=='), ('ne','!=')
    ]:
        exec "def __%s__(self,ob): return self.__subject__ %s ob" % (name, op)

    for name, op in [('neg','-'), ('pos','+'), ('invert','~')]:
        exec "def __%s__(self): return %s self.__subject__" % (name, op)

    for name, op in [
        ('or','|'),  ('and','&'), ('xor','^'), ('lshift','<<'), ('rshift','>>'),
        ('add','+'), ('sub','-'), ('mul','*'), ('div','/'), ('mod','%'),
        ('truediv','/'), ('floordiv','//')
    ]:
        exec (
            "def __%(name)s__(self,ob):\n"
            "    return self.__subject__ %(op)s ob\n"
            "\n"
            "def __r%(name)s__(self,ob):\n"
            "    return ob %(op)s self.__subject__\n"
            "\n"
            "def __i%(name)s__(self,ob):\n"
            "    self.__subject__ %(op)s=ob\n"
            "    return self\n"
        )  % locals()

    del name, op

    # Oddball signatures

    def __rdivmod__(self,ob):
        return divmod(ob, self.__subject__)

    def __pow__(self, *args):
        return pow(self.__subject__, *args)

    def __ipow__(self, ob):
        self.__subject__ **= ob
        return self

    def __rpow__(self, ob):
        return pow(ob, self.__subject__)


class ObjectProxy(AbstractProxy):
    """Proxy for a specific object"""

    __slots__ = "__subject__"

    def __init__(self, subject):
        self.__subject__ = subject


class CallbackProxy(AbstractProxy):
    """Proxy for a dynamically-chosen object"""

    __slots__ = '__callback__'

    def __init__(self, func):
        set_callback(self, func)

set_callback = CallbackProxy.__callback__.__set__
get_callback = CallbackProxy.__callback__.__get__
CallbackProxy.__subject__ = property(lambda self, gc=get_callback: gc(self)())


class LazyProxy(CallbackProxy):
    """Proxy for a lazily-obtained object, that is cached on first use"""
    __slots__ = "__cache__"

get_cache = LazyProxy.__cache__.__get__
set_cache = LazyProxy.__cache__.__set__

def __subject__(self, get_cache=get_cache, set_cache=set_cache):
    try:
        return get_cache(self)
    except AttributeError:
        set_cache(self, get_callback(self)())
        return get_cache(self)

LazyProxy.__subject__ = property(__subject__, set_cache)
del __subject__


class TemplateSafeLazyProxy(LazyProxy):
    """
    A version of LazyProxy suitable for use in Django templates.

    It's important that an ``alters_data`` attribute returns :const:`False`.

    """
    def __getattribute__(self, attr, *args, **kwargs):
        if attr == 'alters_data':
            return False
        return LazyProxy.__getattribute__(self, attr, *args, **kwargs)
