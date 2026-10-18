FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS build
WORKDIR /build
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
ENV VITE_NOETARIS_MODE=live VITE_API_ORIGIN=
RUN npm run build

FROM nginx@sha256:970364228b1e4f932abc22d321932816782cca8a20b85a77552a7cfe9acfb3b5 AS runtime
RUN apk del --no-network curl nginx-module-acme nginx-module-geoip nginx-module-image-filter nginx-module-njs nginx-module-xslt \
 && apk add --no-cache --upgrade zlib=1.3.2-r1 \
 && test ! -e /usr/lib/libxml2.so.2
COPY deploy/nginx.conf /etc/nginx/nsai.conf
COPY --from=build /build/dist /usr/share/nginx/html
FROM scratch
COPY --from=runtime / /
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-c", "/etc/nginx/nsai.conf", "-g", "daemon off;"]
