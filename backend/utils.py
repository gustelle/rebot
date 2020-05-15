# -*- coding: utf-8 -*-

import collections
import text_unidecode
import re
import string

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
    if isinstance(obj, collections.abc.Sequence) and not isinstance(obj, str):
        return True
    return False
