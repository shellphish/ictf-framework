#### General service directory structure

```
services/
        ro - read only  => writable for the ictf user but not by the challenge user
        rw - read/write => writable by the ictf user and by the challenge user
        rr - root owned => not writable by the ictf user and not writable by the service user


./Dockerfile         => Submitted by service creator

./docker-compose.yml => Maintained by iCTF team. Same for every service
```

#### Dockerfile tips

Every service will use the [same docker-compose.yml](https://github.com/Phat3/should-I-rust-or-should-I-go/blob/master/service/docker-compose.yml), which is provided as part of the iCTF infrastructure. As specified in the `docker-compose.yml` file, the directories `./service/ro`, `./service/rw`, and `./service/root_owned` will be "volumed in" at runtime. As such, your Dockerfile will *not* need to COPY in the source code.

The Dockerfile should contain all the instructions necessary to install the dependencies for your service and provision an unprivileged user. The general structure for how to do so is contained [here:](https://github.com/Phat3/should-I-rust-or-should-I-go/blob/master/service/Dockerfile)

In short:

1) Install system dependencies (as root)

2) Create an **unprivileged** user to run the actual service

3) Install any local (userspace) dependencies

4) Finally run the command necessary to start the service (e.g. `CMD cd ./rw && socat tcp-l:6666,reuseaddr,fork exec:"../ro/example_service.py"`)

You are advised to follow [docker best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/).

In particular:

* Keep your images as small as possible
    - only install necessary dependencies
    - delete any intermediate files such as `.tgz`, `/var/lib/apt/lists/*` etc
* Take advantage of docker's build cache by ordering your layers from least frequently changed to most frequent

Note that you can take a look at this [example development history](https://github.com/Phat3/should-I-rust-or-should-I-go/commits/master) to get an idea of the steps required to build your service from scratch.
