FROM python:3.7-bullseye

RUN useradd -ms /bin/bash web

# copy only the files needed for pip install
COPY requirements.txt /home/web/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /home/web/requirements.txt
RUN pip install gevent gevent-websocket


RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash
RUN apt-get install -y nodejs

# copy the rest of the app
COPY . /home/web

WORKDIR /home/web/client

RUN rm -rf node_modules build

RUN npm install

ENV PATH /home/web/client/node_modules/.bin:$PATH

RUN npm run build --openssl-legacy-provider

WORKDIR /home/web

RUN cp -r /home/web/client/build /home/web/server/build

RUN ./gen-cert.sh
RUN chown web:web cert.* && chmod 644 cert.crt && chmod 600 cert.key

USER web
