import boto3
import botocore
import argparse
import docker
from datetime import datetime
import logging

log = logging.getLogger(__name__)

args = argparse.ArgumentParser()

args.add_argument('--docker-image', required=True, help='Name of docker image')
args.add_argument('--bash-command', required=True, help='Bash command to run')
args.add_argument('--aws-cloudwatch-group', required=True, help='Cloudwatch group name')
args.add_argument('--aws-cloudwatch-stream', required=True, help='Cloudwatch stream name')
args.add_argument('--aws-access-key-id', required=True, help='aws access key id')
args.add_argument('--aws-secret-access-key', required=True, help='aws secret access key')
args.add_argument('--aws-region', required=True, help='aws region')


def create_cloudwatch_client(aws_access_key_id, aws_secret_access_key, region_name):
    try:
        return boto3.client('logs', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                            region_name=region_name)
    except botocore.exceptions.EndpointConnectionError:
        log.error("Could not connect to AWS endpoint. Please check your credentials or connection")


def create_group_and_stream(client, log_group_name, log_stream_name):
    try:
        client.create_log_group(logGroupName=log_group_name)
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    except botocore.exceptions.EndpointConnectionError:
        log.error("Could not connect to AWS endpoint. Please check your credentials or connection")
        exit(0)

    try:
        client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    except botocore.exceptions.EndpointConnectionError:
        log.error("Could not connect to AWS endpoint. Please check your credentials or connection")
        exit(0)


def put_log_events(client, log_group_name, log_stream_name, message, sequence_token=None):
    """
    :param client: Клиент CloudWatch Logs.
    :param log_group_name: Имя группы логов.
    :param log_stream_name: Имя log stream.
    :param message: Сообщение для логирования.
    :param sequence_token: Токен последовательности для log stream.
    :return: Возвращает следующий sequence token или None в случае ошибки.
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    log_events = [{
        'timestamp': timestamp,
        'message': message
    }]

    try:
        kwargs = {
            "logGroupName": log_group_name,
            "logStreamName": log_stream_name,
            "logEvents": log_events
        }
        if sequence_token:
            kwargs["sequenceToken"] = sequence_token

        response = client.put_log_events(**kwargs)
        return response.get('nextSequenceToken')
    except client.exceptions.InvalidSequenceTokenException as e:
        log.error(f"Error: {e}, updating sequence token and retrying.")
        return None


def run_container_and_stream_logs(
        image,
        command,
        log_group_name,
        log_stream_name,
        client
):
    docker_client = docker.from_env()
    try:
        container = docker_client.containers.run(image, command, detach=True, stdout=True, stderr=True, stream=True)
    except docker.errors.ImageNotFound:
        log.error("Image not found, please check your image name.")
        exit(0)
    sequence_token = ""
    for stream_log in container.logs(stream=True):
        message = stream_log.decode()
        sequence_token = put_log_events(client, log_group_name, log_stream_name, message, sequence_token)
        print(message) # to see logs in terminal
    container.wait()
    return container


if __name__ == '__main__':
    args = args.parse_args()
    client = create_cloudwatch_client(args.aws_access_key_id, args.aws_secret_access_key, args.aws_region)
    create_group_and_stream(client, args.aws_cloudwatch_group, args.aws_cloudwatch_stream)
    container = run_container_and_stream_logs(args.docker_image,
                                              args.bash_command,
                                              args.aws_cloudwatch_group,
                                              args.aws_cloudwatch_stream,
                                              client
                                              )
    container.remove()
