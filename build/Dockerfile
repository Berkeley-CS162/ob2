# Built from a Ubuntu DIND (Docker In Docker) Image
# https://github.com/teracyhq/docker-files/tree/master/ubuntu/base
FROM teracy/ubuntu:16.04-dind-latest

MAINTAINER cs162@eecs.berkeley.edu

RUN apt-get -y update && apt-get -y install \
	python-pip git python-dev unzip libffi-dev \
	libssl-dev vim sqlite3

RUN pip install --upgrade pip

WORKDIR /ob2
RUN mkdir build

COPY build/requirements.txt build/requirements.txt
RUN pip install -r build/requirements.txt

COPY build/build_apsw.sh build/build_apsw.sh
RUN ./build/build_apsw.sh

COPY ob2 /ob2/ob2

ENTRYPOINT ["python", "-m", "ob2"]
