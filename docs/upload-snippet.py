import os
import requests

# see https://docs.geonode.org/en/master/devel/api/usage/index.html#resource-upload

# url = "https://plasticobs.ni.dfki.de:8001/api/v2/uploads/upload"
url = "http://172.18.0.1:8001/api/v2/uploads/upload"
files = [
    ('base_file', (
        'polygonized_classification_results_dsc01171_crop.zip',
        open(os.path.join(os.path.dirname(__file__), './polygonized_classification_results_dsc01171_crop.zip'), 'rb'),
        'application/octet-stream')),
    ('zip_file', (
        'polygonized_classification_results_dsc01171_crop.zip',
        open(os.path.join(os.path.dirname(__file__), './polygonized_classification_results_dsc01171_crop.zip'), 'rb'),
        'application/octet-stream')),
]
headers = {
    # echo -n "admin:admin" | base64
    'Authorization': 'Basic YWRtaW46YWRtaW4='
}
response = requests.request("POST", url, headers=headers, files=files, data={"overwrite_existing_layer": "true"})

print(response)
