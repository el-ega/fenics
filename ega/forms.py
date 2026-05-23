from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from ega.constants import EMAILS_PLACEHOLDER
from ega.models import (
    ChampionPrediction,
    EgaUser,
    League,
    Match,
    Prediction,
    Team,
)


PENALTY_CHOICES = [('L', _('Local')), ('V', _('Visitante'))]

GOALS_WIDGET = forms.NumberInput(
    attrs={'class': 'form-control', 'min': 0, 'max': 19, 'step': 1}
)


class PredictionFormMixin(object):
    def clean_home_goals(self):
        return self.cleaned_data.get('home_goals')

    def clean_away_goals(self):
        return self.cleaned_data.get('away_goals')

    def validate_prediction(self, cleaned_data):
        home_goals = cleaned_data.get("home_goals")
        away_goals = cleaned_data.get("away_goals")

        msg = "Pronóstico incompleto."
        if home_goals is not None and away_goals is None:
            raise forms.ValidationError(msg)
        if home_goals is None and away_goals is not None:
            raise forms.ValidationError(msg)

        penalties = cleaned_data.get('penalties', '')
        if penalties and home_goals != away_goals:
            msg = _(
                "El ganador de los penales se puede pronosticar sólo con "
                "pronóstico de empate."
            )
            raise forms.ValidationError(msg)

        return (home_goals, away_goals, penalties)


class PredictionForm(PredictionFormMixin, forms.ModelForm):
    home_goals = forms.IntegerField(
        required=False, min_value=0, max_value=19, widget=GOALS_WIDGET
    )
    away_goals = forms.IntegerField(
        required=False, min_value=0, max_value=19, widget=GOALS_WIDGET
    )
    penalties = forms.ChoiceField(
        choices=PENALTY_CHOICES, required=False, widget=forms.RadioSelect()
    )

    def __init__(self, *args, instance=None, initial=None, **kwargs):
        default_prediction = instance and instance.user.default_prediction
        if (
            default_prediction
            and instance.home_goals is None
            and instance.away_goals is None
        ):
            initial = initial or {}
            initial.setdefault('home_goals', default_prediction['home_goals'])
            initial.setdefault('away_goals', default_prediction['away_goals'])
            initial.setdefault('penalties', default_prediction['penalties'])
            self.source = 'preferences'
        super(PredictionForm, self).__init__(
            *args, instance=instance, initial=initial, **kwargs
        )
        self.expired = self.instance.match_id is None
        if not self.expired and self.instance.match.knockout:
            match = self.instance.match
            home = match.home.name if match.home else match.home_placeholder
            away = match.away.name if match.away else match.away_placeholder
            self.fields['penalties'].choices = [('L', home), ('V', away)]

    def clean(self):
        cleaned_data = super(PredictionForm, self).clean()
        (home_goals, away_goals, _) = self.validate_prediction(cleaned_data)
        if home_goals is not None and away_goals is not None:
            cleaned_data['source'] = 'web'
        return cleaned_data

    def save(self, *args, **kwargs):
        if self.expired:
            # ignore predictions we already know expired
            return None

        match = self.instance.match
        if not match.is_expired and self.has_changed():
            return super(PredictionForm, self).save(*args, **kwargs)
        elif match.is_expired:
            self.expired = True
        return None

    class Meta:
        model = Prediction
        fields = ('home_goals', 'away_goals', 'penalties')


class ChampionPredictionForm(forms.ModelForm):
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super(ChampionPredictionForm, self).__init__(*args, **kwargs)
        tournament_teams = self.instance.tournament.teams.order_by('name')
        self.fields['team'].queryset = tournament_teams

    class Meta:
        model = ChampionPrediction
        fields = ('team',)


class InviteFriendsForm(forms.Form):
    emails = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 1,
                'class': 'form-control',
                'placeholder': EMAILS_PLACEHOLDER,
            }
        )
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-control'})
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
                'El email "%s" no es una dirección válida.' % errors[0]
            )
        elif len(errors) > 1:
            raise ValidationError(
                'Los emails "%s" no son direcciones válidas'
                % ', '.join(errors)
            )

        return list(set(emails))

    def invite(self, sender):
        emails = self.cleaned_data['emails']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        return sender.invite_friends(emails, subject, body)


class LeagueForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Nombre'),
    )

    class Meta:
        model = League
        fields = ('name',)


class EgaUserForm(PredictionFormMixin, forms.ModelForm):
    home_goals = forms.IntegerField(
        required=False, min_value=0, max_value=19, widget=GOALS_WIDGET
    )
    away_goals = forms.IntegerField(
        required=False, min_value=0, max_value=19, widget=GOALS_WIDGET
    )
    penalties = forms.ChoiceField(
        choices=PENALTY_CHOICES, required=False, widget=forms.RadioSelect()
    )

    def __init__(self, *args, instance=None, initial=None, **kwargs):
        default_prediction = instance and instance.default_prediction
        if default_prediction:
            initial = initial or {}
            initial['home_goals'] = default_prediction['home_goals']
            initial['away_goals'] = default_prediction['away_goals']
            initial['penalties'] = default_prediction.get('penalties', '')
        super(EgaUserForm, self).__init__(
            *args, instance=instance, initial=initial, **kwargs
        )

    def clean(self):
        cleaned_data = super(EgaUserForm, self).clean()
        (home_goals, away_goals, penalties) = self.validate_prediction(
            cleaned_data
        )
        if home_goals is not None and away_goals is not None:
            default_prediction = (home_goals, away_goals, penalties)
        else:
            default_prediction = None

        # The default_prediction cannot be changed if there is any in progress
        # match
        if self.instance.default_prediction:
            existing_default_prediction = (
                self.instance.default_prediction['home_goals'],
                self.instance.default_prediction['away_goals'],
                self.instance.default_prediction.get('penalties', ''),
            )
        else:
            existing_default_prediction = None
        if (
            default_prediction != existing_default_prediction
            and Match.objects.filter(when__lt=now(), finished=False).exists()
        ):
            raise ValidationError(
                'La predicción por defecto no se puede cambiar si hay '
                'partidos en progreso.'
            )

        cleaned_data['default_prediction'] = default_prediction
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.default_prediction = self.cleaned_data[
            'default_prediction'
        ]
        return super(EgaUserForm, self).save(*args, **kwargs)

    class Meta:
        model = EgaUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'avatar',
            'home_goals',
            'away_goals',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomSignupForm(forms.Form):
    captcha = ReCaptchaField(
        label='', widget=ReCaptchaV3(attrs={'required_score': 0.9})
    )

    def signup(self, request, user):
        """Required, or else it throws deprecation warnings."""
