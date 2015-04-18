# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ega.constants import DEFAULT_TOURNAMENT, EMAILS_PLACEHOLDER
from ega.models import EgaUser, League, Prediction, Tournament


class PredictionForm(forms.ModelForm):
    GOAL_CHOICES = [('', '-')] + [(i, i) for i in range(100)]

    home_goals = forms.ChoiceField(
        choices=GOAL_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control input-lg'}))
    away_goals = forms.ChoiceField(
        choices=GOAL_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control input-lg'}))

    def __init__(self, *args, **kwargs):
        super(PredictionForm, self).__init__(*args, **kwargs)
        self.expired = False

    def _clean_goals(self, field_name):
        goals = self.cleaned_data.get(field_name)
        if not goals:
            goals = None
        return goals

    def clean_home_goals(self):
        return self._clean_goals('home_goals')

    def clean_away_goals(self):
        return self._clean_goals('away_goals')

    def clean(self):
        cleaned_data = super(PredictionForm, self).clean()
        home_goals = cleaned_data.get("home_goals")
        away_goals = cleaned_data.get("away_goals")

        msg = "Pronóstico incompleto."
        if (home_goals and not away_goals):
            self._errors["away_goals"] = self.error_class([msg])
        if (not home_goals and away_goals):
            self._errors["home_goals"] = self.error_class([msg])

        return cleaned_data

    def save(self, *args, **kwargs):
        match = self.instance.match
        if not match.is_expired:
            return super(PredictionForm, self).save(*args, **kwargs)
        else:
            self.expired = True
            return None

    class Meta:
        model = Prediction
        fields = ('home_goals', 'away_goals')


class InviteFriendsForm(forms.Form):

    emails = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': 1, 'class': 'form-control',
                   'placeholder': EMAILS_PLACEHOLDER}))
    subject = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
    )

    def clean_emails(self):
        emails = []
        for email in self.cleaned_data['emails'].split(','):
            emails.extend(e.strip() for e in email.strip().split() if e)

        errors = []
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                errors.append(email)

        if len(errors) == 1:
            raise ValidationError(
                'El email "%s" no es una dirección válida.' % errors[0])
        elif len(errors) > 1:
            raise ValidationError(
                'Los emails "%s" no son direcciones válidas' % ', '.join(
                    errors))

        return list(set(emails))

    def invite(self, sender):
        emails = self.cleaned_data['emails']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        return sender.invite_friends(emails, subject, body)


class LeagueForm(forms.ModelForm):

    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nombre',
    )
    tournament = forms.ModelChoiceField(
        queryset=Tournament.objects.filter(slug=DEFAULT_TOURNAMENT),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Torneo', empty_label=None,
    )

    class Meta:
        model = League
        fields = ('name', 'tournament')


class EgaUserForm(forms.ModelForm):

    class Meta:
        model = EgaUser
        fields = ('username', 'first_name', 'last_name', 'avatar')
