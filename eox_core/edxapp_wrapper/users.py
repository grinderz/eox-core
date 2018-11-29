#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Users public function definitions
"""

from importlib import import_module
from django.conf import settings


def get_edxapp_user(site, *args, **kwargs):
    """ Creates the edxapp user """

    backend_function = settings.EOX_CORE_USERS_BACKEND
    backend = import_module(backend_function)

    return backend.get_edxapp_user(site, *args, **kwargs)


def create_edxapp_user(*args, **kwargs):
    """ Creates the edxapp user """

    backend_function = settings.EOX_CORE_USERS_BACKEND
    backend = import_module(backend_function)

    return backend.create_edxapp_user(*args, **kwargs)


def get_user_read_only_serializer(*args, **kwargs):
    """ Gets the Open edX model UserProfile """

    backend_function = settings.EOX_CORE_USERS_BACKEND
    backend = import_module(backend_function)

    return backend.get_user_read_only_serializer(*args, **kwargs)


def check_edxapp_account_conflicts(*args, **kwargs):
    """ Checks the db for accounts with the same email or password """

    backend_function = settings.EOX_CORE_USERS_BACKEND
    backend = import_module(backend_function)

    return backend.check_edxapp_account_conflicts(*args, **kwargs)
