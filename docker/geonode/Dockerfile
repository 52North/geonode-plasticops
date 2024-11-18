ARG BASE_IMAGE_VERSION
FROM geonode/geonode:${BASE_IMAGE_VERSION}

COPY ./geonode-mapstore-client /usr/src/django_geonode_mapstore_client_dev
RUN yes w | pip install -e /usr/src/django_geonode_mapstore_client_dev

COPY ./requirements.txt /usr/src/more_requirements.txt
RUN yes w | pip install --src /usr/src -r /usr/src/more_requirements.txt

# forward application logs to docker log collector
RUN true \
    && ln -sf /dev/stderr ${CELERY__LOG_FILE:-/var/log/celery.log}

#RUN rm .env*
