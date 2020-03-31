import docker

class RegistryMockup:
    
    def __init__(self):
        self.docker_client = docker.from_env()

    def pull_new_image(self, image_name):
        # Locally we don't have to pull anything since we assume the
        # image to be already present on the system
        #
        # We can think about pushing the image on dockerhub and then pull here
        pass
