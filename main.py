import docker

client = docker.from_env()

# Create a container
container = client.containers.run("alpine", "echo hello world", detach=True)


for log in container.logs(stream=True):
    print(log.decode("utf-8"))

container.stop()
container.remove()
