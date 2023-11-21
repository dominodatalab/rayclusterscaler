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

## Endpoints

This service `http://rayclusterscaler-svc.domino-field/` provides the following endpoints

1. GET `/raycluster/list` - To list all ray clusters which are either owned by the caller or all clusters if an Admin invokes the endpoint
2. GET `/raycluster/<name>` - Get the ray cluster owned by the caller (or any for an admin). Returns `403-Unauthorized` if
the caller tries to retrieve a Ray cluster now permitted to fetch
3. POST `/raycluster/scale` - This scale scales the Ray Cluster. It takes the payload
   ```json
    {
        "cluster_name":"ray-....",
        "replicas" : 5
    }
   ```

Each of these endpoints can be authenticated from inside the workspace by passing a header as follows:

```shell
import requests
import os
access_token_endpoint='http://localhost:8899/access-token'
resp = requests.get(access_token_endpoint)


token = resp.text
headers = {
             "Content-Type": "application/json",
             "Authorization": "Bearer " + token,
        }
#Example
endpoint='http://rayclusterscaler-svc.domino-field/rayclusterscaler/list'
resp = requests.get(endpoint,headers=headers)
```

Alternatively you can also pass the `DOMINO_API_KEY`

```shell
import requests
import os
access_token_endpoint='http://localhost:8899/access-token'
resp = requests.get(access_token_endpoint)
domino_api_key = os.environ['DOMINO_USER_API_KEY']

token = resp.text
headers = {
             "Content-Type": "application/json",
             "X-Domino-Api-Key": domino_api_key,
        }
#Example
endpoint='http://rayclusterscaler-svc.domino-field/rayclusterscaler/list'
resp = requests.get(endpoint,headers=headers)
```


## Note on the scale endpoint

When you call the scale endpoint follow up with the GET `/raycluster/<name>` endpoint to verify that the cluster has 
scaled. This information is obtained by the checking the `status` section of the returned `json` which should appear
something like this

```json
"status": {
        "clusterStatus": "Running",
        "nodes": [
          "ray-655cb2de368ad4624b1e7d7b-ray-head-0",
          "ray-655cb2de368ad4624b1e7d7b-ray-worker-0",
          "ray-655cb2de368ad4624b1e7d7b-ray-worker-1",
          "ray-655cb2de368ad4624b1e7d7b-ray-worker-2",
          "ray-655cb2de368ad4624b1e7d7b-ray-worker-3",
          "ray-655cb2de368ad4624b1e7d7b-ray-worker-4"
        ],
        "startTime": "2023-11-21T13:38:58Z",
        "workerReplicas": 5,
        "workerSelector": "app.kubernetes.io/component=worker,app.kubernetes.io/instance=ray-655cb2de368ad4624b1e7d7b,app.kubernetes.io/name=ray"
      }
```

Additionally verify that the `spec.autoscaling` section reflects the scale correctly. For a scaling number of `5` the
values for the `minReplicas` and `maxReplicas` should be as below

```json
"autoscaling": {
          "maxReplicas": 6,
          "minReplicas": 5
        }
```

Lastly, the `spec.worker.replicas` attribute in the above example should be equal to the value for `minReplicas` (`5` in our example)

> Also make sure you review the Ray Cluster UI to verify that every worker has joined the cluster before launching the
> job. The `RayCluster` CRD will indicate running pods. Only the Ray Cluster UI (or API) will confirm that the workers
> have joined the cluster
> 