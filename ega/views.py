import twitter

from allauth.account.forms import LoginForm, SignupForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from ega.forms import InviteFriendsForm, PredictionForm
from ega.models import EgaUser, League, Prediction, Tournament


def get_absolute_url(url):
    return Site.objects.get_current().domain + url


def soon(request):
    return render(request, 'ega/soon.html')


@login_required
def home(request):
    return render(request, 'ega/home.html')


@require_http_methods(('GET', 'POST'))
@login_required
def invite_friends(request):
    invite_url = get_absolute_url(
        reverse('join', kwargs=dict(key=request.user.invite_key)))
    if request.method == 'POST':
        form = InviteFriendsForm(invite_url, request.POST)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            request.user.invite_friends(emails, subject, body)
            if len(emails) > 1:
                msg = '%s amigos invitados!' % len(emails)
            else:
                msg = '1 amigo invitado!'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = InviteFriendsForm(invite_url)

    return render(request, 'ega/invite.html', dict(form=form))


@require_http_methods(('GET', 'POST'))
def friend_join(request, key, league=None):
    friend = get_object_or_404(EgaUser, invite_key=key)

    if league:
        league = get_object_or_404(League, slug=league)

    if request.method == 'POST':
        messages.success(request, 'Te uniste a el Ega!')
        return HttpResponseRedirect(reverse('home'))

    register_form = SignupForm(email_required=True)  # UserCreationForm()
    login_form = LoginForm()  # AuthenticationForm()
    context = dict(
        friend=friend, register_form=register_form, login_form=login_form)
    return render(request, 'ega/join.html', context)


@login_required
def next_matches(request, slug):
    """Return coming matches for the speficied tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    matches = tournament.next_matches()
    # select related positions
    for m in matches:
        # create prediction for user if missing
        Prediction.objects.get_or_create(user=request.user, match=m)
        # get trends (save pred L E V?))

    PredictionFormSet = modelformset_factory(
        Prediction, form=PredictionForm, extra=0)

    if request.method == 'POST':
        formset = PredictionFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('ega-next-matches', args=[slug]))
    else:
        predictions = Prediction.objects.filter(
            user=request.user, match__in=matches)
        formset = PredictionFormSet(queryset=predictions)

    return render(
        request, 'ega/next_matches.html',
        {'tournament': tournament, 'formset': formset})
