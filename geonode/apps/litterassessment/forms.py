from django import forms

CHOICES = [
    ('densenet_121', 'densenet_121'),
    ('maskrcnn_resnet50', 'maskrcnn_resnet50'),
    ('festival_pld', 'festival_pld'),
    ('vis_ai', 'vis_ai'),
]

class TriggerAiInferenceForm(forms.Form):
    model = forms.ChoiceField(choices=CHOICES, required=True)
    ids = forms.CharField(required=False, widget=forms.HiddenInput())
