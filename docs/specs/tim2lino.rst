.. _cosi.specs.tim2lino:

==================
Importing from TIM
==================

..  to test only this document:

    $ python setup.py test -s tests.DocsTests.test_tim2lino

    >>> import lino
    >>> lino.startup('lino_cosi.projects.std.settings.doctests')
    >>> from lino.api.doctest import *
    >>> from django.db.models import Q


>>> from lino_cosi.lib.tim2lino.utils import TimLoader
>>> tim = TimLoader('', 'en')
>>> tim.dc2lino("D")
True
>>> tim.dc2lino("C")
False

>>> tim.dc2lino("A")
True
>>> tim.dc2lino("E")
False
