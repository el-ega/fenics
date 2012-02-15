# -*- coding: utf-8 -*-
from django.contrib import admin

from models import UserProfile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

admin.site.register(UserProfile, ProfileAdmin)
