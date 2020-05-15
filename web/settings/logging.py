# -*- coding: utf-8 -*-

import os
import errno
import logging
from logging.config import dictConfig

import config

def _get_logfile(filename):
    """Logfile factory
    """
    log_dir = os.path.abspath(
        os.path.sep.join([os.path.realpath(__file__), '..', '..', 'logs']))

    try:
        os.makedirs(log_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    return os.path.abspath(
        os.path.join(
            log_dir, filename))

def _get_dict_config(log_level):
    """
    """
    dict_config = {
        'version': 1,
        'formatters': {
            'app_formatter': {
                'format' : '%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s: %(message)s'
            }
        },
        'handlers': {
            'app_handler': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'app_formatter',
                'level': log_level,
                'filename': _get_logfile('app.log'),
                'when': 'midnight',
                'interval': 1,
                'backupCount': 5
            },
            'console_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'app_formatter',
                'level': logging.INFO
            },
            'elasticsearch_handler': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'app_formatter',
                'level': logging.INFO,
                'filename': _get_logfile('elasticsearch.log'),
                'when': 'midnight',
                'interval': 1,
                'backupCount': 5
            },
            # 'elasticsearch_trace_handler': {
            #     'class': 'logging.handlers.TimedRotatingFileHandler',
            #     'formatter': 'app_formatter',
            #     'level': logging.DEBUG,
            #     'filename': _get_logfile('elasticsearch-trace.log'),
            #     'when': 'midnight',
            #     'interval': 1,
            #     'backupCount': 5
            # }
            'elasticsearch_trace_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'app_formatter',
                'level': logging.INFO
            }

        },
        'loggers': {
            'app':  {
                'level': log_level,
                'handlers': ['app_handler', 'console_handler'],
            },
            'elasticsearch':  {
                'level': logging.ERROR,
                'handlers': ['elasticsearch_handler'],
            },
            'elasticsearch.trace': {
                'level': logging.ERROR,
                'handlers': ['elasticsearch_trace_handler'],
            }
        }
    }
    return dict_config


dictConfig(_get_dict_config(
    config.ENV.LOG_LEVEL
))
