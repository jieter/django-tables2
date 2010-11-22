"""Global module options.

I'm not entirely happy about these existing at this point; maybe we can
get rid of them.
"""


__all__ = ('options',)


# A common use case is passing incoming query values directly into the
# table constructor - data that can easily be invalid, say if manually
# modified by a user. So by default, such errors will be silently
# ignored. Set the option below to False if you want an exceptions to be
# raised instead.
class DefaultOptions(object):
    IGNORE_INVALID_OPTIONS = True
options = DefaultOptions()
