"""Domino rayclusterscaler_api module Module.

This module implements a functions/endpoints for rayscaler_api api.

Example:
    List raycluster(GET) : /raycluster/list
    Get raycluster(GET) : /raycluster/<name>
    Patch raycluster(POST) : /raycluster/<name>


"""
from typing import Dict

import requests
from flask import request, Response, Blueprint  # type: ignore
import logging
from kubernetes import client, config
from kubernetes.client import ApiClient, CustomObjectsApi
import os


rayclusterscaler_api = Blueprint("rayclusterscaler_api", __name__)

DEFAULT_COMPUTE_NAMESPACE = "domino-compute"
k8s_api_client = None
k8s_api = None
group = "distributed-compute.dominodatalab.com"
version = "v1alpha1"
compute_namespace = "domino-compute"
plural = "rayclusters"


compute_namespace: str = os.environ.get(
    "COMPUTE_NAMESPACE", DEFAULT_COMPUTE_NAMESPACE
)

WHO_AM_I_ENDPOINT = "v4/auth/principal"
DOMINO_NUCLEUS_URI = os.environ.get("DOMINO_NUCLEUS_URI","http://nucleus-frontend.domino-platform:80")


lvl: str = logging.getLevelName(os.environ.get("LOG_LEVEL", "WARNING"))
logging.basicConfig(
    level=lvl,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rayclusterscaling")
logger.setLevel(logging.WARNING)

try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except config.ConfigException:
        raise Exception("Could not configure kubernetes python client")

k8s_api_client: ApiClient = client.ApiClient()
k8s_api: CustomObjectsApi = client.CustomObjectsApi(k8s_api_client)
debug: bool = os.environ.get("FLASK_ENV") == "development"


def get_headers(headers):
    new_headers = {}
    if "X-Domino-Api-Key" in headers:
        new_headers["X-Domino-Api-Key"] = headers["X-Domino-Api-Key"]
    elif "Authorization" in headers:
        new_headers["Authorization"] = headers["Authorization"]
    return new_headers


def get_user(headers):
    url: str = os.path.join(DOMINO_NUCLEUS_URI, WHO_AM_I_ENDPOINT)
    ret: Dict = requests.get(url, headers=headers)
    is_admin: bool = False
    canonical_id:str = ''
    if ret.status_code == 200:
        user: str = ret.json()
        user_name: str = user["canonicalName"]
        logger.warning(f"Calling User {user_name}")
        if not user['isAnonymous']:
            canonical_id:str = user["canonicalId"]
        is_admin: bool = user["isAdmin"]
    return is_admin,canonical_id

def is_authorized_to_view_ray_cluster(caller_canonical_id:str,is_admin:bool,raycluster_owner_id:str):
    is_auth = is_admin or caller_canonical_id==raycluster_owner_id;
    logger.warning(f'Calling User {caller_canonical_id} with Admin Status {is_admin} '
                   f'Ray cluster owner {raycluster_owner_id}. Authorized ={is_auth} ')
    return is_auth

@rayclusterscaler_api.route("/rayclusterscaler/scale", methods=["POST"])
def scale_raycluster() -> object:
    try:
        scale_config = request.get_json()
        logging.warning(scale_config)
        raycluster_name = scale_config['cluster_name']
        replicas = scale_config['replicas']
        out: object = k8s_api.get_namespaced_custom_object(
            group, version, compute_namespace, plural, raycluster_name
        )
        raycluster_owner_id = out['metadata']['labels']['dominodatalab.com/starting-user-id']
        admin, canonical_user_id= get_user(get_headers(request.headers))
        if is_authorized_to_view_ray_cluster(canonical_user_id, admin, raycluster_owner_id):
            if not 'autoscaling' in out['spec']:
                return Response(
                    "Cannot scale this cluster. Autoscaling not enabled",
                    404,
                )
            else:
                print(replicas)
                out['spec']['autoscaling']['maxReplicas']= (replicas + 1)
                out['spec']['autoscaling']['minReplicas'] = replicas
                out['spec']['worker']['replicas'] = replicas
                out: object = k8s_api.patch_namespaced_custom_object(
                    group, version, compute_namespace, plural, raycluster_name, out
                )

            return out
        else:
            return Response(
                "Unauthorized to update the ray cluster. Not a owner or admin",
                403,
            )
    except Exception as e:
        logger.exception(e)



@rayclusterscaler_api.route("/rayclusterscaler/<name>", methods=["GET"])
def get_raycluster(name: str) -> object:
    try:
        logger.warning(request.headers)
        out: object = k8s_api.get_namespaced_custom_object(
            group, version, compute_namespace, plural, name
        )
        raycluster_owner_id = out['metadata']['labels']['dominodatalab.com/starting-user-id']
        admin, canonical_user_id= get_user(get_headers(request.headers))
        if is_authorized_to_view_ray_cluster(canonical_user_id,admin,raycluster_owner_id):
            return out
        else:
            return Response(
                f"Not authorized to access ray cluster {name}. Not ray cluster owner or domino admin",
                403,
            )
    except Exception as e:
        logger.exception(e)
        logger.warning(f"Mutation {name} failed to delete")


@rayclusterscaler_api.route("/rayclusterscaler/list", methods=["GET"])
def list_rayclusters():
    logger.warning("/rayclusterscaler/list")
    try:
        raycluster_lst =  k8s_api.list_namespaced_custom_object(
                group, version, compute_namespace, plural
        )
        rayclusters = raycluster_lst['items']
        ret_list = []
        admin, canonical_user_id = get_user(get_headers(request.headers))

        for r in rayclusters:
            raycluster_owner_id = r['metadata']['labels']['dominodatalab.com/starting-user-id']
            if is_authorized_to_view_ray_cluster(canonical_user_id, admin, raycluster_owner_id):
                ret_list.append(r)
        return {'ray_clusters' :ret_list}
    except Exception as e:
        logger.exception(e)
        return Response(
            f"Failed to list ray clusters" + str(e),
            500,
        )
