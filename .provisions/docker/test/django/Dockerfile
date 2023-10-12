# define an alias for the specfic python version used in this file.
FROM python:3.11.3-slim-bullseye as python

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT=development

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev

# Install pipenv
RUN  pip install --upgrade pip && pip install pipenv

# Requirements are installed here to ensure they will be cached.
#COPY ./requirements .

COPY Pipfile Pipfile.lock ./
#RUN pipenv install --deploy --system

RUN pipenv requirements --dev > requirements.txt

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels -r requirements.txt


# Python 'run' stage
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=development

ARG USER_UID=1000
ARG GROUP_GID=1000
ARG USER_NAME=app

ARG GROUP_NAME=app
ARG HOME_DIR=/home/${USER_NAME}

ARG USER

ARG APP_FOLDER=/app
ARG APP_PATH=/var${APP_FOLDER}

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_PATH}

# explicitly set user/group IDs
RUN set -eux; \
	groupadd -r ${GROUP_NAME} --gid=${GROUP_GID}; \
	useradd -r ${USER_NAME} -g ${GROUP_NAME} --home-dir=${HOME_DIR} --uid=${USER_UID}; \
    mkdir -p ${HOME_DIR} ; \
	chown -R ${USER_NAME}:${GROUP_NAME} ${HOME_DIR}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Gpg keys \
  gnupg \
  # helper for requests
  curl \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
	&& rm -rf /wheels/


USER ${USER_NAME}


# copy application code to WORKDIR
COPY . ${APP_PATH}

CMD ["python",  "manage.py", "runserver_plus", "0.0.0.0:8000"]
