from django.urls import re_path

from litterassessment.views import ForwardToInferenceApi, BatchInferenceApi

urlpatterns = [
    re_path(r"$", BatchInferenceApi.as_view()),
    re_path(r"^(?P<path>.*)/$", ForwardToInferenceApi.as_view()),
]
