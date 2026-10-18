"""Authlib cache adapter: browser-bound PostgreSQL state, consumed once."""
import asyncio
import hashlib
import json
import re

from . import store


class PostgresStateCache:
    def __init__(self, browser_hash, *, context=None):
        if not isinstance(browser_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', browser_hash):
            raise ValueError('Invalid authentication browser binding')
        self.browser_hash = browser_hash
        self.context=dict(context) if context is not None else None
        self.consumed=None

    @staticmethod
    def _key(key):
        if not isinstance(key, str) or not re.fullmatch(r'_state_(?:google|github)_[a-zA-Z0-9_-]{20,128}', key):
            raise ValueError('Invalid authentication state key')
        if store.request_identity() is not None:
            raise PermissionError('Authentication state requires service context')
        return hashlib.sha256(key.encode('ascii')).hexdigest()

    def _put(self, key, value):
        state_hash = self._key(key)
        if not isinstance(value, str) or not 1 <= len(value.encode('utf-8')) <= 8192:
            raise ValueError('Invalid authentication state payload')
        if self.context is not None:
            data=json.loads(value)
            data['data']['nsai_context']=self.context
            value=json.dumps(data,separators=(',',':'))
            if len(value.encode('utf-8'))>8192:raise ValueError('Authentication state exceeds budget')
        with store.connect() as conn:
            if self.context is not None:
                epoch=self.context.get('browser_epoch')
                if type(epoch) is not int or epoch<1:raise ValueError('Missing browser authentication epoch')
                conn.execute('SELECT nsai_oauth_browser_assert(%s,%s)',(self.browser_hash,epoch))
            conn.execute('SELECT nsai_oauth_state_put(%s,%s,%s)', (state_hash, self.browser_hash, value))

    def _take(self, key):
        state_hash = self._key(key)
        with store.connect() as conn:
            return conn.execute('SELECT nsai_oauth_state_take(%s,%s)', (state_hash, self.browser_hash)).fetchone()[0]

    def _clear(self, key):
        state_hash = self._key(key)
        with store.connect() as conn:
            conn.execute('SELECT nsai_oauth_state_clear(%s,%s)', (state_hash, self.browser_hash))

    async def set(self, key, value, expires_in):
        if expires_in != 300:
            raise ValueError('Authentication state lifetime must be five minutes')
        await asyncio.to_thread(self._put, key, value)

    async def get(self, key):
        value=await asyncio.to_thread(self._take, key)
        if value is not None:self.consumed=json.loads(value).get('data')
        return value

    async def delete(self, key):
        await asyncio.to_thread(self._clear, key)
