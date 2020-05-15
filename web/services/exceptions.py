# -*- coding: utf-8 -*-


class CatalogNotFoundError(Exception):
    """Raised when a catalog is not found
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class ServiceError(Exception):
    """Generic technical error
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class InitializationError(ServiceError):
    """Raised when a class is badly initialized
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
