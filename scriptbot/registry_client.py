from settings import LOGSTASH_IP, LOGSTASH_PORT
import settings

import docker
import logging
import logstash

class RegistryClientPullError(Exception):
    pass

class RegistryClient:
    def __init__(self,
        registry_username=settings.REGISTRY_USERNAME,
        registry_password=settings.REGISTRY_PASSWORD,
        registry_endpoint=settings.REGISTRY_ENDPOINT):

        self.registry_username = registry_username
        # FIXME: The login token will expire! we need to refresh it if we want a game that
        #        last more than 8 hours. Getting a token requires AWS APIs though and
        #        we don't want a script to be bounded by the time this takes.
        self.registry_password = registry_password
        self.registry_endpoint = registry_endpoint
        self.docker_client = docker.from_env()
        self.log = logging.getLogger('scriptbot.registryClient')
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        if not settings.IS_LOCAL_REGISTRY:
            self._authenticate()

    def _authenticate(self):
        self.docker_client.login(
            username=self.registry_username,
            password=self.registry_password,
            registry="https://{}".format(self.registry_endpoint)
        )

    def pull_new_image(self, image_name, image_path):
        try:
            if not settings.IS_LOCAL_REGISTRY:
                self.log.info("Pulling new image {} from {}...".format(image_name, image_path))
                res = self.docker_client.images.pull(image_path)
                self.log.info("Pulled image {}: {}".format(image_name, res))
            else:
                self.log.info("The framework is running locally... there is no need to pull the image {}".format(image_name))
        except docker.errors.APIError as ex:
            raise RegistryClientPullError("Error during pull of {}: {}".format(image_name, ex))
