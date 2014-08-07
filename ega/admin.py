from django.contrib import admin

from ega.models import (
    EgaUser,
    League,
    LeagueMember,
    Match,
    Prediction,
    Team,
    TeamStats,
    Tournament,
)


class LeagueMemberInline(admin.TabularInline):
    model = LeagueMember
    extra = 0


class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    inlines = [LeagueMemberInline]


class TeamAdmin(admin.ModelAdmin):

    prepopulated_fields = dict(slug=('name',))


class TournamentAdmin(admin.ModelAdmin):
    filter_horizontal = ('teams',)
    prepopulated_fields = dict(slug=('name',))


admin.site.register(EgaUser)
admin.site.register(League, LeagueAdmin)
admin.site.register(Match)
admin.site.register(Prediction)
admin.site.register(Team, TeamAdmin)
admin.site.register(TeamStats)
admin.site.register(Tournament, TournamentAdmin)
