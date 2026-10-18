#!/bin/sh
set -eu
umask 077
password=$(cat /run/secrets/redis_password)
case "$password" in ''|*[!A-Za-z0-9_-]*) exit 1;; esac
[ "${#password}" -ge 32 ] && [ "${#password}" -le 128 ]
{
 printf 'bind 0.0.0.0\nport 6379\nprotected-mode yes\n'
 printf 'requirepass %s\n' "$password"
 printf 'maxmemory 64mb\nmaxmemory-policy noeviction\n'
 printf 'save ""\nappendonly no\ndir /tmp\n'
 printf 'rename-command CONFIG ""\nrename-command FLUSHALL ""\nrename-command FLUSHDB ""\n'
} > /tmp/nsai-redis.conf
unset password
exec redis-server /tmp/nsai-redis.conf
