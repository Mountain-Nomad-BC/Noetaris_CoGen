"""Opaque dependency references are reauthorized at every resolution."""
import re
from . import store


def register(sources,*,conn=None):
    if conn is None:
        with store.connect() as owned:return register(sources,conn=owned)
    return conn.execute('SELECT nsai_register_source_manifest(%s)',(sources,)).fetchone()[0]


def get_sources(manifest_id,*,conn=None):
    if not isinstance(manifest_id,str) or not re.fullmatch('[a-f0-9]{32}',manifest_id):
        raise ValueError('Invalid source manifest reference')
    if conn is None:
        with store.connect() as owned:return get_sources(manifest_id,conn=owned)
    return conn.execute('SELECT nsai_source_manifest_sources(%s)',(manifest_id,)).fetchone()[0]
