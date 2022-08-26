FROM node:16
COPY staticContent /srv/phoenix
RUN cd /srv/phoenix && yarn && yarn build

FROM python:3.8-alpine

RUN mkdir -p /srv/phoenixRest && addgroup -S phoenixRest && adduser -S phoenixRest -G phoenixRest; \
chown phoenixRest:phoenixRest /srv/phoenixRest; \
mkdir -p /files; chmod 777 /files;

# TODO this is dumb, should probably not be a common thing. We badly want separate prod and development images
WORKDIR /srv/phoenixRest
COPY . /srv/phoenixRest
COPY --from=0 /srv/phoenix/public/static /srv/phoenixRest/phoenixRest/static

RUN rm -r staticContent && apk add --no-cache postgresql-libs libpng libjpeg; \
apk add --no-cache --virtual .build-deps build-base libffi-dev postgresql-dev jpeg-dev zlib-dev libpng-dev; \
rm -r docker && pip install -e . && pip install psycopg2; \
mv alembic-docker.ini alembic.ini; \
chmod +x /srv/phoenixRest/docker-startup.sh && \
mkdir /uploads && chown phoenixRest /uploads; \
apk del .build-deps;

COPY ./docker/common/wait-for-it.sh /srv/phoenixRest/

USER phoenixRest
EXPOSE 8080

ENTRYPOINT ["sh", "/srv/phoenixRest/docker-startup.sh"]
CMD ["pserve", "paste_prod.ini"]