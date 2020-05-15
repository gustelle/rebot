# -*- coding: utf-8 -*-

import os
import logging
import re
import string
import collections

import text_unidecode

from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from sanic import response
from sanic.exceptions import abort

from sanic_babel import gettext

import config

#############################################################################
# constants
LOGGER = logging.getLogger("app")


def safe_text(text, replace_with='', strict=True):
    """
    Remove special chars for sensitive storage systems
    the text returned contains only valid chars (no special one)

    Solution inspired from https://stackoverflow.com/questions/23996118/replace-special-characters-in-a-string-python#23996414

    :param strict: if False white spaces are OK
    :param replace_with: the char that replaces the special chars. Default is ''
    """
    if text is None:
        return None

    _intermediate = text_unidecode.unidecode(text).strip().lower()
    chars = re.escape(string.punctuation)
    if strict:
        full = re.sub(r'['+chars+']', replace_with, _intermediate)
    else:
        full = re.sub(r'['+chars+']', replace_with, _intermediate)

    # remove all duplicate blank spaces
    return re.sub('\s+', ' ', full).strip()



def is_list(obj):
    if obj is None:
        return False
    if isinstance(obj, collections.abc.Sequence) and not isinstance(obj, str):
        return True
    LOGGER.debug(f"Object {obj} provided is not a list, type : {type(obj)}")
    return False


async def render_template(template_file, **args):
    """
    simulate the flask render_template
    """
    def _static_file(filename):
        """
        shortcut for static folder in templates
        the URL should be relative because joined with the root url of the app

        Take a look to the app statup config, which sets the static folder under the '/' url path

        :Example':
        >>> _static_file('style.css')
        /static/style.css
        """
        return f"/static/{filename}"

    # Load the template with async support
    CWD = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    template_env = Environment(
        loader=FileSystemLoader([
            os.path.sep.join([CWD, 'blueprints', 'templates'])
        ]),
        autoescape=select_autoescape(['html', 'xml']),
        enable_async=True)

    template_env.globals.update({ 'static': _static_file, 'gettext': gettext })
    template = template_env.get_template(template_file)
    rendered_template = await template.render_async(args)
    return response.html(rendered_template)
