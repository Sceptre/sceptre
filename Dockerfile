FROM python:3.6-alpine

#
# a simple image for running Sceptre without installing Python
#
# to build it:
#   $ docker build . -t sceptre-local
#
# to then deploy it to Dockerhub after version X.Y.Z is released:
#   $ docker login
#   $ docker tag sceptre-local rgitzel/sceptre:X.Y.Z
#   $ docker push rgitzel/sceptre:X.Y.Z
#
# if it's the newest version:
#   $ docker tag sceptre-local rgitzel/sceptre:latest
#   $ docker push rgitzel/sceptre:latest


# we'll copy the repo files to here
ARG SRC_FOLDER="/src"

# expect the folder of Sceptre files to be mounted here
ARG SCEPTRE_FOLDER="/sceptre"

# copy the relevant files
RUN mkdir $SRC_FOLDER
COPY contrib $SRC_FOLDER/contrib
COPY HISTORY.rst $SRC_FOLDER
COPY Makefile $SRC_FOLDER
COPY README.rst $SRC_FOLDER
COPY requirements.txt $SRC_FOLDER
COPY sceptre $SRC_FOLDER/sceptre
COPY setup.* $SRC_FOLDER/

# install from those files
RUN pip install -e $SRC_FOLDER

# Sceptre files should be here
VOLUME ["$SCEPTRE_FOLDER"]
WORKDIR $SCEPTRE_FOLDER

ENTRYPOINT [ "sceptre" ]
