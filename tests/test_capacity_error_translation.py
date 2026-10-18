import pytest
from fastapi import HTTPException
from psycopg.errors import ProgramLimitExceeded
from nsai.api import translate_error


def test_database_capacity_error_is_actionable_without_private_details():
    with pytest.raises(HTTPException) as caught:
        translate_error(ProgramLimitExceeded('other-owner-canary has private usage'))
    assert caught.value.status_code==409
    assert 'capacity' in caught.value.detail.lower()
    assert 'other-owner-canary' not in caught.value.detail
