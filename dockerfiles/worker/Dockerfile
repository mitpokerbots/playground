FROM python:3.7-bullseye

RUN useradd -ms /bin/bash worker

# copy only the files needed for pip install
COPY requirements.txt /home/worker/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /home/worker/requirements.txt

COPY requirements-worker.txt /home/worker/requirements-worker.txt
RUN pip install --no-cache-dir -r /home/worker/requirements-worker.txt

ENV DEBIAN_FRONTEND noninteractive

RUN echo 'deb http://ftp.debian.org/debian bullseye-backports main' >> /etc/apt/sources.list.d/sources.list
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get -t bullseye-backports install -yq openjdk-11-jdk-headless
RUN apt-get install -yq gcc g++ scons autoconf libtool libboost-all-dev libc6-dev

USER worker

# copy the rest of the app
COPY . /home/worker

WORKDIR /home/worker
