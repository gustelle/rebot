import copy
import uuid

import pytest
from unittest.mock import patch

import utils


async def test_safe_text_default(monkeypatch, mocker, dataset):
    """"""

    assert utils.safe_text("my?_# text") == "mytext"


async def test_safe_text_accept(monkeypatch, mocker, dataset):
    """try accepting some chars"""

    assert utils.safe_text("my?_# text", accept=["_", " "]) == "my_ text"
