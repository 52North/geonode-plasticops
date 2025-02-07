import json
import logging

from django.utils import timezone
from geonode.resource.models import ExecutionRequest
from geonode.utils import http_client
from geonode.celery_app import app

from litterassessment.models import Inference

logger = logging.getLogger(__name__)

QUEUE = "geonode"

POLLABLE_STATES = [
    Inference.Status.PENDING,
    Inference.Status.RUNNING,
]

@app.task(queue=QUEUE)
def background_trigger_inference(exec_id: str):
    from litterassessment.views import _trigger_inference
    _exec = ExecutionRequest.objects.filter(exec_id=exec_id)
    if not _exec.exists():
        logger.error(f"Execution request '{exec_id}' not found")
        return
    execution_request = _exec.first()
    input_params = execution_request.input_params
    
    resource = execution_request.geonode_resource
    access_token = input_params["access_token"]
    wms_url = input_params["wms_url"]
    model = input_params["model"]
    job = _trigger_inference(
        execution_request.user,
        path=f"models/{model}/",
        payload={
            "pk": str(resource.pk),
            "title": resource.title,
            "imageUrl": f"{wms_url}&access_token={access_token}"
        },
        resource=resource)

@app.task(queue=QUEUE)
def poll_inference_status():
    inferences = Inference.objects.filter(status__in = POLLABLE_STATES)
    for inference in inferences:
        url = inference.job_url
        if not url:
            logger.info("Delete invalid inference without job URL.")
            inference.delete()
            continue
        
        response, _ = http_client.get(url)
        inference.updated = timezone.now()
        
        if response.status_code == 404:
            inference.status = Inference.Status.DELETED
        elif response:
            content = response.json()
            status = content["status"]
            message = content["msg"]
            
            try:
                inference_status = Inference.Status[status.upper()]
                if not inference_status in POLLABLE_STATES:
                    inference.finish(inference_status, message)
                else:
                    inference.status = inference_status
            except KeyError:
                logger.error(f"Received unknown status: '{status}'")
            inference.details = message
            
        else:
            logging.error(f"Error polling inference status of '{inference.job_url}'")
        
        inference.save()
        