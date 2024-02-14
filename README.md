# Test project
Project to allow to run dockers and pass their logs to aws logs

## How to run
```bash
pip3 install -r requirements.txt
python3 main.py --docker-image python --bash-command "/bin/bash -c 'pip install --upgrade pip && pip install '" --aws-cloudwatch-group test-task-group1 --aws-cloudwatch-stream test-task-stream-1 --aws-access-key-id [Your AWS Access Key ID] --aws-secret-access-key [Your AWS Secret Access Key] --aws-region eu-central-1
```
