from django import forms

from ega.models import Prediction


class PredictionForm(forms.ModelForm):
    GOAL_CHOICES = [('', '-')] + [(i,i) for i in range(10)]

    home_goals = forms.ChoiceField(
        choices=GOAL_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-control input-lg'}))
    away_goals = forms.ChoiceField(
        choices=GOAL_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-control input-lg'}))

    def _clean_goals(self, field_name):
        goals = self.cleaned_data.get(field_name)
        if not goals:
            goals = None
        return goals

    def clean_home_goals(self):
        return self._clean_goals('home_goals')

    def clean_away_goals(self):
        return self._clean_goals('away_goals')

    class Meta:
        model = Prediction
        fields = ('home_goals', 'away_goals')


class InviteFriendsForm(forms.Form):

    emails = forms.CharField()

    def clean_emails(self):
        cleaned_data = super(InviteFriendsForm, self).clean_fields()
        emails = map(str.strip, cleaned_data['emails'].split(','))
        for e in emails:
            validate_email(e)

        return cleaned_data
