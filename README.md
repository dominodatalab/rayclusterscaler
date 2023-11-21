# Ray Cluster Custom Scaler (Beta)
This is a basic Ray Cluster Scaler



## Installation

If `domino-field` namespace is not present create using below command

```shell
kubectl create namespace domino-field
kubectl label namespace domino-field  domino-compute=true
kubectl label namespace domino-field  domino-platform=true
```

```shell
export field_namespace=domino-field
helm install -f ./values.yaml rayclusterscaler helm/rayclusterscaler -n ${field_namespace}
```
## Upgrade

```shell
export field_namespace=domino-field

helm upgrade -f ./values.yaml rayclusterscaler helm/rayclusterscaler -n ${field_namespace}
```

## Delete 

```shell
export field_namespace=domino-field
helm delete  rayclusterscaler -n ${field_namespace}
```

