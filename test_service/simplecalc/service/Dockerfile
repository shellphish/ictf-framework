FROM ubuntu:18.04

RUN apt-get update && apt-get install -y xinetd libc6-i386

RUN useradd -u 31337 -ms /bin/bash chall
RUN chown root:root /home/chall
RUN chmod 755 /home/chall

COPY ./ro/xinetd.conf /etc/xinetd.d/simplecalc
RUN chmod 644 /etc/xinetd.d/simplecalc

WORKDIR /home/chall/service

# Locally we have to run as root to test until we have a proper infrastructure 
# USER chall

CMD ["/usr/sbin/xinetd", "-dontfork"]
