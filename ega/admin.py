from django.contrib import admin

from ega.models import League, Match, Prediction, Team, Tournament


admin.site.register(League)
admin.site.register(Match)
admin.site.register(Prediction)
admin.site.register(Team)
admin.site.register(Tournament)
