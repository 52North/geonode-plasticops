from django.contrib import admin
from django.shortcuts import render

from geonode.base.admin import metadata_batch_edit
from geonode.layers.admin import DatasetAdmin
from geonode.layers.models import Dataset

from litterassessment.forms import TriggerAiInferenceForm


admin.site.unregister(Dataset)


def raster_trigger_inference(modeladmin, request, queryset):
    ids = ",".join(str(element.pk) for element in queryset)
    form = TriggerAiInferenceForm({"ids": ids})
    return render(
        request, "litterassessment/trigger_inference.html", context={"form": form, "ids": ids}
    )


class AiInferenceDatasetAdmin(DatasetAdmin):
    
    actions = [
        metadata_batch_edit,
        raster_trigger_inference,
    ]
    
    def has_module_permission(self, request):
        return (
            request.user.is_superuser
            or request.user.has_perm("litterassessment.can_trigger_inference")
        )
    
    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_superuser
            or request.user.has_perm("litterassessment.can_trigger_inference")
        )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # TODO relax to "can_view"
        # view_resourcebase
        return qs.filter(owner=request.user)


admin.site.register(Dataset, AiInferenceDatasetAdmin)
