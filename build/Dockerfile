# Built from a Ubuntu DIND (Docker In Docker) Image
# https://github.com/teracyhq/docker-files/tree/master/ubuntu/base
FROM teracy/ubuntu:16.04-dind-latest
MAINTAINER cs162@eecs.berkeley.edu

RUN apt-get -y update && apt-get -y install \
	python-pip git python-dev unzip libffi-dev \
	libssl-dev vim sqlite3

WORKDIR /ob2

COPY build/requirements.txt /ob2
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY build/build_apsw.sh /ob2
RUN ./build_apsw.sh

COPY ob2 /ob2/ob2

ENTRYPOINT ["python", "-m", "ob2"]
