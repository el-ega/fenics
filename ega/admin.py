from django.contrib import admin

from ega.models import (
    EgaUser,
    League,
    LeagueMember,
    Match,
    MatchEvents,
    Prediction,
    Team,
    TeamStats,
    Tournament,
)


class EgaUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'invite_key', 'date_joined')
    search_fields = ('username', 'email', 'invite_key')
    readonly_fields = ('list_referrals',)

    def list_referrals(self, obj):
        return ', '.join(u.username for u in obj.referrals.all())


class LeagueMemberInline(admin.TabularInline):
    model = LeagueMember
    extra = 0


class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    inlines = [LeagueMemberInline]


class TeamAdmin(admin.ModelAdmin):
    prepopulated_fields = dict(slug=('name',))


class TeamStatsAdmin(admin.ModelAdmin):
    list_filter = ('tournament', 'team')


class MatchAdmin(admin.ModelAdmin):
    list_filter = ('tournament', 'when')


class PredictionAdmin(admin.ModelAdmin):
    list_filter = ('match__tournament', 'user')


class TournamentAdmin(admin.ModelAdmin):
    filter_horizontal = ('teams',)
    prepopulated_fields = dict(slug=('name',))


admin.site.register(EgaUser, EgaUserAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(MatchEvents)
admin.site.register(Prediction, PredictionAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(TeamStats, TeamStatsAdmin)
admin.site.register(Tournament, TournamentAdmin)
