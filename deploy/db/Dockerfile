# Current Postgres 16.15 base, retained by digest. Remove obsolete Go helper and refresh libraries.
FROM postgres:16-alpine@sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea AS hardened
COPY deploy/db/apk-package-closure.lock /opt/apk-package-closure.lock
# Pin every target package including the base's local virtual meta-package.
# Reject a downgrade before installation; require the entire resulting closure
# to match exactly. Repository signature verification remains APK's default.
RUN awk '/^P:/{name=substr($0,3)} /^V:/{print name "=" substr($0,3)}' /lib/apk/db/installed | sort > /tmp/base-packages \
    && while IFS='=' read -r name version; do \
         current=$(awk -F= -v key="$name" '$1==key {print $2}' /tmp/base-packages); \
         if [ -n "$current" ] && [ "$(apk version -t "$current" "$version")" = '>' ]; then echo "Pinned package would downgrade: $name" >&2; exit 1; fi; \
       done < /opt/apk-package-closure.lock \
    && xargs apk add --no-cache --upgrade < /opt/apk-package-closure.lock \
    && awk '/^P:/{name=substr($0,3)} /^V:/{print name "=" substr($0,3)}' /lib/apk/db/installed | sort > /tmp/actual-packages \
    && diff -u /opt/apk-package-closure.lock /tmp/actual-packages \
    && sed -i 's/exec gosu postgres/exec \/sbin\/su-exec postgres/g' /usr/local/bin/docker-entrypoint.sh \
    && rm -f /usr/local/bin/gosu /usr/local/bin/su-exec \
    && test -x /sbin/su-exec

# Copy only the merged, patched filesystem. Removed helpers and superseded library layers
# must not remain distributable in the final artifact or its software inventory.
FROM scratch
COPY --from=hardened / /
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    LANG=en_US.utf8 PG_MAJOR=16 PG_VERSION=16.15 PGDATA=/var/lib/postgresql/data
VOLUME ["/var/lib/postgresql/data"]
EXPOSE 5432
STOPSIGNAL SIGINT
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
