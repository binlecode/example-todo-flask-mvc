the following steps are used to deploy the app to a kubernetes cluster in digitalocean:

- create a kubernetes cluster in digitalocean
- install `doctl` cli tool
- install `kubectl` cli tool
- install `helm` cli tool
- install public load balancer using helm

use doctl to create a kubernetes cluster in digitalocean:

```sh
# check do account info
doctl auth list
doctl account get

# check existing clusters
doctl kubernetes cluster list

# add cluster to kubectl context
doctl kubernetes cluster kubeconfig save do-k8s
```

The kubernetes deployment is based on the docker image pushed to docker hub
image registry.

```sh
# create namespace
kubectl create namespace todo-flask-mvc
# create deployment
kubectl create deployment todo-flask-mvc -n todo-flask-mvc --image=ikalidocker/example-todo-flask-mvc
# check deployment
kubectl get deployments -n todo-flask-mvc

# create a nodeport service for deployment todo-flask-mvc
# with targetPort 5000 and port 80
kubectl expose deployment todo-flask-mvc --type=NodePort \
  --target-port=5000 --port 80 --namespace todo-flask-mvc \
  --name=todo-flask-mvc-service
# check services
kubectl get service -n todo-flask-mvc
```

To delete deployment:

```sh
kubectl delete service todo-flask-mvc
kubectl delete deployment todo-flask-mvc
```

## install k8s nginx ingress for public load balancer

To access the deployed service:

- ensure public load balancer is installed
- create an nginx ingress resource to route from external load balancer to the service

Install public load balancer by nginx ingress controller using helm:

```sh
# check helm repos
helm repo list
# add helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
# update helm repo
helm repo update
# install ingress controller
helm install -n default nginx-ingress ingress-nginx/ingress-nginx --set controller.publishService.enabled=true

# check the creation of load balancer service
kubectl -n default get services -o wide -w nginx-ingress-ingress-nginx-controller

# check ingress controller
kubectl get pods -n default
# check ingress controller service
kubectl get service -n default
```

To remove the external loadbalancer nginx ingress controller:

```sh
helm uninstall nginx-ingress -n default
```

## install k8s ingress resource

Install with manifest yaml file that contains routing rules:

```sh
kubectl apply -f k8s/ingress.yaml
# check ingress
kubectl get ingress -n todo-flask-mvc
```

## update deployment config for ingress path prefix

The ingress resource introduces a path prefix `/todo-flask-mvc` to the service, therefore, the application needs to know this for url routing.

This is done by setting the `SCRIPT_NAME` environment variable in the deployment config, for wsgi gunicorn webserver to configure the application routing path prefix.

```sh
kubectl edit configmap todo-flask-mvc-configmap -n todo-flask-mvc

```







## Appendix - Ingress that makes use of the controller:

```yaml
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: example
    namespace: foo
  spec:
    ingressClassName: nginx
    rules:
      - host: www.example.com
        http:
          paths:
            - pathType: Prefix
              backend:
                service:
                  name: exampleService
                  port:
                    number: 80
              path: /
    # This section is only required if TLS is to be enabled for the Ingress
    tls:
      - hosts:
        - www.example.com
        secretName: example-tls

If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:

  apiVersion: v1
  kind: Secret
  metadata:
    name: example-tls
    namespace: foo
  data:
    tls.crt: <base64 encoded cert>
    tls.key: <base64 encoded key>
  type: kubernetes.io/tls
````
