import json
import logging

from django.utils import timezone
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
def batch_trigger_inferences(request, model, resources, access_token):
    from litterassessment.views import _trigger_inference
    for resource in resources:
        wms_url = resource.link_set.filter(name="PNG")[0].url
        job = _trigger_inference(
            request,
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