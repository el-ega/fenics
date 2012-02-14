# -*- coding: utf-8 -*-
from django.contrib import admin

from models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published')
    search_fields = ('title',)

admin.site.register(News, NewsAdmin)
