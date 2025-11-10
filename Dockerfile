# Prepare the base environment.
FROM ghcr.io/dbca-wa/docker-apps-dev:ubuntu_2404_base_python as builder_base_queuemanager

MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Australia/Perth
ENV PRODUCTION_EMAIL=True
ENV SECRET_KEY="ThisisNotRealKey"
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
# RUN apt-get install --no-install-recommends -y wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata libreoffice cron rsyslog gunicorn virtualenv
# RUN apt-get install --no-install-recommends -y libpq-dev patch
# RUN apt-get install --no-install-recommends -y postgresql-client mtr
# RUN apt-get install --no-install-recommends -y sqlite3 vim postgresql-client ssh htop
# RUN ln -s /usr/bin/python3 /usr/bin/python 

# RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
# RUN chmod 755 /tmp/default_script_installer.sh
# RUN /tmp/default_script_installer.sh

RUN groupadd -g 5000 oim 
RUN useradd -g 5000 -u 5000 oim -s /bin/bash -d /app
RUN mkdir /app 
RUN chown -R oim:oim /app 

COPY startup.sh /
COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN chmod 755 /startup.sh


# Install Python libs from requirements.txt.
FROM builder_base_queuemanager as python_libs_queuemanager
WORKDIR /app
USER oim
RUN virtualenv /app/venv
ENV PATH=/app/venv/bin:$PATH
RUN git config --global --add safe.directory /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt 

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_queuemanager


# COPY cron /etc/cron.d/dockercron


# RUN chmod 0644 /etc/cron.d/dockercron
# RUN crontab /etc/cron.d/dockercron
# RUN touch /var/log/cron.log
# RUN service cron start
COPY .git ./.git

COPY --chown=oim:oim gunicorn.ini manage.py ./
RUN touch /app/.env
COPY --chown=oim:oim queuemanager ./queuemanager
COPY --chown=oim:oim django_site_queue ./django_site_queue
COPY --chown=oim:oim python-cron ./

RUN mkdir /app/queuemanager/cache/
RUN chmod 777 /app/queuemanager/cache/
RUN python manage.py collectstatic --noinput

USER root
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*
USER oim

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]


