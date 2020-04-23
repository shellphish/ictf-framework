FROM ubuntu:16.04

ARG ictfuser
ARG ictfuserpassword

RUN useradd -m -c 'ICTF infrastructure user' -G sudo $ictfuser -s /bin/bash && \
    echo $ictfuser:$ictfuserpassword | chpasswd

RUN apt-get update -y