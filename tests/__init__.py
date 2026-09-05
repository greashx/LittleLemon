"""Test package init.

Python 3.14 + Django 4.1 compatibility fix: ``copy.copy`` on a
``RequestContext`` fails because ``super().__copy__()`` in
``django.template.context.Context.__copy__`` returns a ``super`` proxy
that no longer has a writable ``__dict__``. We rebind ``__copy__`` on the
base ``Context`` class to a safe shallow-copy implementation.
"""
import django.template.context as _ctx


def _safe_copy(self):
    return self.__class__(self.dicts[:])


_ctx.Context.__copy__ = _safe_copy
