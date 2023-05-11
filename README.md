### Prerequisites
1. Docker
2. Kubernetes

### Start the service
- Optional. If prefer to use Kubernetes secrets, run `$ sh ./prepare/create_secrets.sh`
- Create a deployment for the database service. `$ kubectl apply -f ./kubernetes/deployments/db.yaml`
- Create a deployment for the authentication service. `$ kubectl apply -f ./kubernetes/deployments/auth.yaml`
- Create a deployment for the url shortner service. `$ kubectl apply -f ./kubernetes/deployments/urlshortner.yaml`
- Create a service for the database service. `$ kubectl apply -f ./kubernetes/services/db.yaml`
- Create a service for the authentication service. `$ kubectl apply -f ./kubernetes/services/auth.yaml`
- Create a service for the url shortner service. `$ kubectl apply -f ./kubernetes/services/urlshortner.yaml`
- Optional. If prefer to use Ingress, run `kubectl apply -f ./kubernetes/ingress/appingress.yaml`
