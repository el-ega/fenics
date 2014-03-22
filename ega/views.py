from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from ega.forms import PredictionForm
from ega.models import Prediction, Tournament


@login_required
def next_matches(request, slug):
    """Return coming matches for the speficied tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    # create predictions for user, then get formset
    matches = tournament.next_matches()
    for m in matches:
        Prediction.objects.get_or_create(user=request.user, match=m)
    predictions = Prediction.objects.filter(match__in=matches)

    PredictionFormSet = modelformset_factory(
        Prediction, form=PredictionForm, extra=0)

    if request.method == 'POST':
        formset = PredictionFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('ega-next-matches', args=[slug]))
    else:
        formset = PredictionFormSet(queryset=predictions)

    return TemplateResponse(
        request, 'ega/next_matches.html', {'formset': formset})
