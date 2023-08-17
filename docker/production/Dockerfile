FROM node:16
COPY staticContent /srv/phoenix
RUN cd /srv/phoenix && yarn && yarn build

FROM python:3.10-alpine

RUN mkdir -p /srv/phoenixRest && addgroup -S phoenixRest && adduser -S phoenixRest -G phoenixRest; \
chown phoenixRest:phoenixRest /srv/phoenixRest; \
mkdir -p /files; chmod 777 /files;

# TODO this is dumb, should probably not be a common thing. We badly want separate prod and development images
WORKDIR /srv/phoenixRest
COPY . /srv/phoenixRest
COPY --from=0 /srv/phoenix/public/static /srv/phoenixRest/phoenixRest/static

RUN ./install-deps-alpine.sh && mkdir /uploads && chown phoenixRest /uploads

COPY ./docker/common/wait-for-it.sh /srv/phoenixRest/

USER phoenixRest
EXPOSE 8080

ENTRYPOINT ["sh", "/srv/phoenixRest/docker-startup.sh"]
CMD ["gunicorn", "--workers=6", "--paste", "paste_prod.ini", "-b", ":8080"]
