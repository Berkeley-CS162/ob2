import docker
# from docker.utils import create_host_config
from requests.exceptions import ConnectionError, ReadTimeout

import ob2.config as config


class DockerClient(object):
    def __init__(self, sock="unix://var/run/docker.sock"):
        self.client = docker.DockerClient(base_url=sock, version="auto")

    def clean(self):
        containers = self.client.containers.list(all=True)
        for container in containers:
            container.remove(v=True, force=True)
        self.client.images.prune(filters={'dangling': True})

    def start(self, image, mem_limit="1024m", memswap_limit="1024m", labels=[], volumes={},
              max_procs=256, max_files=256, keep_container=False):
        """
        Starts a new container and returns the container ID for use.

        image      -- The docker image to use as a base
        mem_limit  -- The memory limit
        labels     -- A list of strings to label this container.
        volumes    -- A dictionary of {local_path: remote_path} of mounts to install on the
                      container.
        max_procs  -- The ulimit nproc
        max_files  -- The ulimit nofile
        keep_container -- Do not delete Docker container after running

        """
        converted_volumes = {}
        for local_path, remote_path in volumes.items():
            converted_volumes[local_path] = {'bind': remote_path, 'mode': 'rw'}
        run_config = {
            'image': image,
            # TODO: figure out why uncommenting causes OOM killer
            'mem_limit': mem_limit, 
            'memswap_limit': memswap_limit,
            "network_mode": "bridge",
            # "oom_kill_disable": True,
            'labels': labels,
            'volumes': converted_volumes,
            'ulimits': [
                docker.types.Ulimit(name='nproc', soft=max_procs, hard=max_procs),
                docker.types.Ulimit(name='nofile', soft=max_files, hard=max_files),
                docker.types.Ulimit(name='nice', soft=5, hard=5)
            ],
            'detach': True,
            'security_opt': ["apparmor:%s" % config.dockergrader_apparmor_profile] if config.dockergrader_apparmor_profile else [],
            'tty': True,
            'command': "/bin/bash"
        }

        container = self.client.containers.run(**run_config)
        return Container(self, container.id, keep_alive=keep_container)

    def stop(self, container_id, v=True, force=True):
        """
        Kills and destroys a container.

        v     -- Also removes the volumes associated with the container.
        force -- Stops container if it is running.

        """
        self.client.remove_container(container_id, v=v, force=force)

    def run_command(self, container_id, command, timeout=10):
        try:
            exec_instance = self.client.containers.get(container_id).exec_run(
                cmd=command, stdout=True, stderr=True, tty=False
            )
            output = exec_instance.output
            return output
        except docker.errors.APIError as e:
            raise RuntimeError(f"Error executing command: {e}")
        except docker.errors.ContainerError as e:
            raise RuntimeError(f"Command failed in container: {e}")
        except docker.errors.NotFound as e:
            raise RuntimeError(f"Container not found: {e}")

    def bash(self, container_id, payload, user="root", timeout=10):
        return self.run_command(container_id, ["su", "-c", payload, "-s", "/bin/bash", user],
                                timeout)


class Container(object):
    def __init__(self, docker_client, container_id, keep_alive=False):
        """A convenience object that represents a single container."""
        self.docker_client = docker_client
        self.container_id = container_id
        self.keep_alive = keep_alive

    def run_command(self, *args, **kwargs):
        return self.docker_client.run_command(self.container_id, *args, **kwargs)

    def bash(self, *args, **kwargs):
        return self.docker_client.bash(self.container_id, *args, **kwargs)

    def stop(self, *args, **kwargs):
        return self.docker_client.stop(self.container_id, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self.keep_alive:
            self.stop()


class TimeoutError(Exception):
    pass
