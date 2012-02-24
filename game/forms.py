# -*- coding: utf-8 -*-
from datetime import datetime

from django import forms
from django.forms.models import BaseModelFormSet

from game.models import Card, Match


SCORE_CHOICES = [('', '-')] + [(i,i) for i in range(10)]


class BaseCardForm(forms.ModelForm):
    match = forms.ModelChoiceField(queryset=Match.objects.all(),
                                   widget=forms.HiddenInput)
    starred = forms.BooleanField(required=False,
                                 widget=forms.HiddenInput)
    home_goals = forms.TypedChoiceField(choices=SCORE_CHOICES,
                                        coerce=int, empty_value='', required=False,
                                        widget=forms.Select(attrs={'class':'score-select'}))
    away_goals = forms.TypedChoiceField(choices=SCORE_CHOICES,
                                        coerce=int, empty_value='', required=False,
                                        widget=forms.Select(attrs={'class':'score-select'}))


    class Meta:
        model = Card
        fields = ('match', 'starred', 'home_goals', 'away_goals')

    def clean_home_goals(self):
        data = self.cleaned_data.get('home_goals', '')
        if data == '':
            data = None
        return data

    def clean_away_goals(self):
        data = self.cleaned_data.get('away_goals', '')
        if data == '':
            data = None
        return data

    def clean(self):
        super(BaseCardForm, self).clean()
        cleaned_data = self.cleaned_data

        # validate deadline expiration
        now = datetime.now()
        if now > self.instance.match.deadline:
            raise forms.ValidationError("El tiempo para jugar el partido %s "
                                        "expiró." % self.instance.match)
        return self.cleaned_data


class BaseCardFormSet(BaseModelFormSet):

    def __init__(self, user, tournament, *args, **kwargs):
        self.user = user

        # create match/user cards if needed
        playable = Match.currently_playable.filter(group__tournament=tournament)

        for match in playable:
            card, created = Card.objects.get_or_create(match=match, user=user)

        queryset = Card.objects.filter(user=user, match__in=playable
                    ).order_by('match__date')

        # HACK: Django bug: https://code.djangoproject.com/ticket/17478
        if 'queryset' not in kwargs.keys():
            kwargs['queryset'] = queryset

        super(BaseCardFormSet, self).__init__(*args, **kwargs)

    def has_errors(self):
        # any of the forms has errors?
        return any(self.errors)

    #def clean(self):
        ## check user has stars available
        #pass

