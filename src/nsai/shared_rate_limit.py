"""Atomic Redis request windows; durable generation accounting remains PostgreSQL-owned."""
import hashlib
import hmac
import os
import re
from uuid import uuid4
from urllib.parse import urlsplit
from .store import _secret

SCRIPT="""
local stamp=redis.call('TIME')
local now=tonumber(stamp[1])*1000000+tonumber(stamp[2])
redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',now-60000000)
if redis.call('ZCARD',KEYS[1])>=tonumber(ARGV[1]) then return 0 end
redis.call('ZADD',KEYS[1],now,ARGV[2])
redis.call('EXPIRE',KEYS[1],61)
return 1
"""

AUTH_SCRIPT="""
local stamp=redis.call('TIME')
local now=tonumber(stamp[1])*1000000+tonumber(stamp[2])
for i=1,3 do
 redis.call('ZREMRANGEBYSCORE',KEYS[i],'-inf',now-60000000)
 if redis.call('ZCARD',KEYS[i])>=tonumber(ARGV[i]) then return 0 end
end
for i=1,3 do
 redis.call('ZADD',KEYS[i],now,ARGV[4]);redis.call('EXPIRE',KEYS[i],61)
end
return 1
"""


def backend():
    setting=os.getenv('NSAI_RATE_LIMIT_BACKEND','local')
    if setting not in {'local','redis'}:raise ValueError('Invalid rate limit backend')
    return setting


def settings():
    url=os.getenv('NSAI_REDIS_URL','redis://redis:6379')
    try:
        parts=urlsplit(url);port=parts.port or 6379
    except ValueError:raise ValueError('Invalid Redis endpoint') from None
    if (parts.scheme not in {'redis','rediss'} or not parts.hostname or parts.username or parts.password
            or parts.path not in {'','/'} or parts.query or parts.fragment):
        raise ValueError('Invalid Redis endpoint')
    if parts.scheme=='redis' and parts.hostname not in {'redis','localhost','127.0.0.1'}:
        raise ValueError('Remote Redis requires authenticated TLS')
    password=_secret(os.environ['NSAI_REDIS_PASSWORD_FILE'])
    return parts.hostname,port,parts.scheme=='rediss',password


def admit(actor,limit):
    if (not isinstance(actor,str) or re.fullmatch(r'local-(?:operator|viewer|reviewer|admin|user-[a-z][a-z0-9_-]{0,63})',actor) is None):
        return False
    if type(limit) is not int or not 1<=limit<=10000:raise ValueError('Invalid request allowance')
    import redis
    host,port,tls,password=settings()
    key='nsai:requests:1:'+hmac.new(password.encode(),actor.encode(),hashlib.sha256).hexdigest()
    # A bounded connection is closed after each operation. No credentials are
    # retained in cache keys or connection error reports returned to the client.
    options=dict(host=host,port=port,password=password,decode_responses=True,
                 socket_timeout=.75,socket_connect_timeout=.75,ssl=tls)
    if tls:options['ssl_cert_reqs']='required';options['ssl_check_hostname']=True
    try:
        with redis.Redis(**options) as client:
            result=client.eval(SCRIPT,1,key,limit,uuid4().hex)
            if result not in (0,1):raise RuntimeError('Invalid coordination response')
            return result==1
    except redis.exceptions.RedisError:
        raise RuntimeError('Shared rate limiting unavailable') from None


def validate_runtime():
    selected=backend()
    from .operation_admission import enabled
    operations=enabled()
    if os.getenv('K_SERVICE') and selected!='redis':
        raise ValueError('Cloud Run requires shared rate limiting')
    if os.getenv('K_SERVICE') and not operations:
        raise ValueError('Cloud Run requires durable operation coordination')
    if selected=='redis':settings()


def admit_auth(digests,limits):
    """Atomic global/peer/browser admission; keys contain only opaque HMACs."""
    if (len(digests)!=3 or len(set(digests))!=3
            or any(not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{64}',value) for value in digests)
            or len(limits)!=3 or any(type(value) is not int or not 1<=value<=1000 for value in limits)):
        raise ValueError('Invalid authentication request allowance')
    import redis
    host,port,tls,password=settings()
    options=dict(host=host,port=port,password=password,decode_responses=True,
                 socket_timeout=.75,socket_connect_timeout=.75,ssl=tls)
    if tls:options['ssl_cert_reqs']='required';options['ssl_check_hostname']=True
    try:
        with redis.Redis(**options) as client:
            result=client.eval(AUTH_SCRIPT,3,*['nsai:auth:1:'+digest for digest in digests],*limits,uuid4().hex)
            if result not in (0,1):raise RuntimeError('Invalid coordination response')
            return result==1
    except redis.exceptions.RedisError:
        raise RuntimeError('Shared authentication rate limiting unavailable') from None
