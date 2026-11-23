# Chatterbox 🎉

A small asyncio TCP chat server and a colorful terminal client.
Commands: `/nick /who /me /roll 2d20 /8ball /shrug /help /quit`.

## Run locally
```
python -m chatterbox.server            # terminal 1
python -m chatterbox.client            # terminal 2, 3, ...
pip install -r requirements-dev.txt && pytest
```

## Docker
```
docker build -t chatterbox .
docker run --rm -p 5000:5000 chatterbox
```

## Deploy to AWS (EKS)
```
aws ecr create-repository --repository-name chatterbox
aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
docker tag chatterbox <acct>.dkr.ecr.<region>.amazonaws.com/chatterbox:v1
docker push <acct>.dkr.ecr.<region>.amazonaws.com/chatterbox:v1
# edit image: in k8s/deployment.yaml, then:
kubectl apply -f k8s/
kubectl get svc chatterbox     # wait for the NLB hostname (EXTERNAL-IP)
python -m chatterbox.client <nlb-hostname> 5000
```
The Service uses an NLB, so the AWS Load Balancer Controller must be installed in the cluster.

## Scaling note
Chat state is in memory, so keep `replicas: 1`. To scale out, add Redis pub/sub between pods.
