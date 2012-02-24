# -*- coding: utf-8 -*-
from django.contrib import admin

from models import (Team, Tournament, Match, MatchGroup, Card, UserPosition,
                    TeamPosition)


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name', )

admin.site.register(Team, TeamAdmin)


class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('teams',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name', )

admin.site.register(Tournament, TournamentAdmin)


class MatchInline(admin.TabularInline):
    model = Match


class MatchGroupAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'name',)
    list_filter = ('tournament',)
    search_fields = ('name', )
    ordering = ('name', )
    inlines = [MatchInline]
admin.site.register(MatchGroup, MatchGroupAdmin)


class MatchAdmin(admin.ModelAdmin):
    list_display = ('group', 'home', 'home_goals', 'away_goals', 'away', 'date')
    list_filter = ('approved', 'group', 'date')
    search_fields = ('home__name', 'away__name')
    ordering = ('group', )
    fieldsets = (
        (None, {
            'fields': ('group',)
        }),
        ('Match Info', {
            'fields': ('location', 'referee', 'date', 'home', 'home_goals',
                       'away', 'away_goals', 'approved')
        }),
    )
admin.site.register(Match, MatchAdmin)


class CardAdmin(admin.ModelAdmin):
    list_display = ('user', 'match')
    search_fields = ('user__username',)
    ordering = ('match', 'user')
admin.site.register(Card, CardAdmin)


class UserPositionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tournament', 'points')
    list_filter = ('tournament',)
    search_fields = ('user__username',)
    ordering = ('order',)
admin.site.register(UserPosition, UserPositionAdmin)


class TeamPositionAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'team', 'pts', 'pg', 'pe', 'pp', 'dg', 'gf', 'gc')
    list_filter = ('tournament',)
    search_fields = ('team__name',)
    ordering = ('order',)
admin.site.register(TeamPosition, TeamPositionAdmin)
