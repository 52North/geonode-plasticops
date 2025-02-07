import json
import logging
import asyncio

from django.shortcuts import render
from django.conf import settings
from django.http import (
    HttpResponseRedirect,
    HttpResponseServerError,
    JsonResponse,
)

from geonode.base.models import ResourceBase
from geonode.base.auth import get_or_create_token
from geonode.base.views import get_url_for_model
from geonode.resource.models import ExecutionRequest
from geonode.layers.models import Dataset
from geonode.utils import http_client

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound, APIException
from oauth2_provider.contrib import rest_framework

from litterassessment.models import Inference
from litterassessment.forms import TriggerAiInferenceForm
from litterassessment.tasks import background_trigger_inference
from litterassessment.permissions import CanTriggerInferencePermissions
from litterassessment.apps import LITTERASSESSMENT_MODEL_API

logger = logging.getLogger(__name__)


def _forward_url(path):
    api_url = getattr(settings, LITTERASSESSMENT_MODEL_API)
    return f"{api_url}/{path}"


def _forward(method, path, headers={}, data=None):
    url = _forward_url(path)
    response, content = http_client.request(
        url, method, data=data, headers=headers, verify=False
    )
    if response:
        status_code = response.status_code 
        if status_code >= 200 and status_code < 400:
            return response
        if status_code == 400:
            raise ValidationError(response.content)
        elif status_code == 404:
            raise NotFound(response.content)
        else:
            raise APIException(response.content)
    else:
        logger.warning(f"Could not process request! -> {content}")
        return HttpResponseServerError("Error processing request.")

def _trigger_inference(user, path, payload, resource):
    
    inference = Inference.objects.create(payload=payload, resource=resource)
    inference.group_id = payload["inferenceGroup"] if "inferenceGroup" in payload else None
    inference.initiator = user
    inference.save()

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps(payload)
    response = _forward("POST", path, headers=headers, data=data)

    if not response:
        return None
    
    job = response.json()
    if response.status_code == 201:
        inference.job_url = response.headers["location"]
        status = job["status"]
        if status == "running":
            inference.set_running()
    else:
        message = job["msg"]
        inference.finish(Inference.Status.FAILED)
        inference.details(f"Job status: {status}, Details: '{message}'")
        
    inference.save()
    return job

class ForwardToInferenceApi(APIView):
    authentication_classes = [
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
        rest_framework.OAuth2Authentication,
    ]
    permission_classes = [
        CanTriggerInferencePermissions
    ]
    
    def get(self, request, path, format=None):
        if request.method == "GET":
            headers = {"Accept": "application/json"}
            response = _forward("GET", path, headers=headers)
            return JsonResponse(response.json())

    def post(self, request, path):
        if isinstance(request.data, dict):
            payload = request.data
        else:
            try:
                payload = json.loads(request.data)
            except Exception as e:
                logger.debug("Invalid JSON payload!", e)
                raise ValidationError("Invalid JSON payload!")

        if "pk" not in payload:
            raise ValidationError("Missing pk of resource")

        # check user permissions before forwarding request
        pk = payload["pk"]
        try:
            resource = ResourceBase.objects.get(pk=pk).get_self_resource()
            if not request.user.has_perm("base.view_resourcebase", resource):
                raise PermissionDenied("Invalid permissions to access resource!")
        except ResourceBase.DoesNotExist:
            raise ValidationError(f"Resource with id '{pk}' does not exist!")

        # inference = Inference.objects.create(payload=payload, resource=resource)
        # inference.group_id = payload["inferenceGroup"] if "inferenceGroup" in payload else None
        # inference.initiator = request.user
        # inference.save()

        # headers = {"Content-Type": "application/json", "Accept": "application/json"}
        # data = json.dumps(payload)
        # response = _forward("POST", path, headers=headers, data=data)
        
        job = _trigger_inference(request.user, path, payload, resource)

        if not job:
            return JsonResponse(data={
                "status": 500,
                "error": "Some error occured!"
            })
        
        return JsonResponse(job)


class BatchInferenceApi(APIView):
    authentication_classes = [
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
        rest_framework.OAuth2Authentication,
    ]
    permission_classes = [
        CanTriggerInferencePermissions
    ]

    def post(self, request):
        if not (
                request.user.is_superuser
                or request.user.has_perm("litterassessment.can_trigger_inference")
        ):
            raise PermissionDenied
        
        template = "litterassessment/trigger_inference.html"
        ids = request.POST.get("ids")

        if "cancel" in request.POST or not ids:
            return HttpResponseRedirect(get_url_for_model("dataset"))

        if request.method == "POST":
            form = TriggerAiInferenceForm(request.POST)
            if form.is_valid():
                ids = form.cleaned_data.pop("ids")
                model = form.cleaned_data.pop("model")

                access_token = get_or_create_token(request.user)
                resources = Dataset.objects.filter(id__in=ids.split(","))
                
                for resource in resources:
                    wms_url = resource.link_set.filter(name="PNG")[0].url
                    # _trigger_inference(request.user, f"models/{model}/", {
                    #     "pk": str(resource.pk),
                    #     "title": resource.title,
                    #     "imageUrl": f"{wms_url}&access_token={access_token}",
                    # }, resource)
                    exec = ExecutionRequest.objects.create(
                        user=request.user,
                        geonode_resource=resource,
                        func_name=_trigger_inference,
                        input_params={
                            "model": model,
                            "wms_url": wms_url,
                            "access_token": str(access_token)
                        }
                    )
                    background_trigger_inference.delay(exec.exec_id)
                
                return HttpResponseRedirect("/inferences")

            return render(
                request,
                template,
                context={
                    "form": form,
                    "ids": ids,
                    "model": model,
                },
            )

        form = TriggerAiInferenceForm()
        return render(
            request,
            template,
            context={
                "form": form,
                "ids": ids,
                "model": model,
            },
        )