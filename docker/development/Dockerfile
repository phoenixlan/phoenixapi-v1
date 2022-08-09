FROM python:3.8

RUN mkdir -p /srv/phoenixRest && groupadd -r phoenixRest && useradd -r -g phoenixRest phoenixRest; \
chown phoenixRest:phoenixRest /srv/phoenixRest

# TODO this is dumb, should probably not be a common thing. We badly want separate prod and development images
WORKDIR /srv/phoenixRest
COPY . /srv/phoenixRest

RUN rm -r docker && pip install -e . && pip install psycopg2; \
rm -r phoenixRest; mv alembic-docker.ini alembic.ini; \
chmod +x /srv/phoenixRest/docker-startup.sh && \
mkdir /uploads && chown phoenixRest /uploads

COPY ./docker/common/wait-for-it.sh /srv/phoenixRest/

USER phoenixRest
EXPOSE 8080
ENV PYRAMID_DEBUG_AUTHORIZATION=1 PYRAMID_DEBUG_ROUTEMATCH=1 

ENTRYPOINT ["bash", "/srv/phoenixRest/docker-startup.sh"]
CMD ["pserve", "paste_develop.ini", "--reload"]
