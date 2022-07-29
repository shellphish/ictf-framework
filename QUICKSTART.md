# Setting up the environment

First, start by creating a virtualenv and installing all required dependencies
```bash
mkvirtualenv ictf
./install_all_requirements ~/.virtualenvs/ictf
```

# Set up game configuration

Let's start by either using an existing `game_config.json` (e.g. the one from `ictf-test-ctf-1`) or creating one from
scratch following the example from `game_config.example.json`. For the `"teams"` list, a set of dummy teams (2) suffices
for now to test. This should eventually be populated by your registration mechanism.

Secondly, we need to create game secrets (database passwords, API keys, etc) using the `make_secrets.sh` script.

```bash
cp ../ictf-test-ctf-1/game_config.json ./
./make_secrets.sh
```

# iCTF build system

The build system is split into 2 stages: Build (`hephaestus/`, god of the forge) + Deploy (`ares/`, god of war(-games))


# Building the `teamvm`
First, we start by building the `teamvm` as it builds separately from the rest of the infrastructure.

```bash
cd hephaestus/docker
python ./build_teamvm.py ../../game_config.json
```

This will spit out a `docker-compose` command for you to run, do that now!

E.g.
```bash
docker-compose -f ./docker-compose-teamvm.yml build --build-arg services='{"SERVICES": ["atm_machine", "sharing", "tweety_bird"]}'
```

If this all succeeded, you should now have built a working `teamvm` image!

# Shortcut for local docker-compose game deploy

Now that the teamvm is built, you can use the helper-command

```
./go.sh
```

which should ideally spin up a full game for you.
