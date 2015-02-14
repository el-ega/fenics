from django.contrib import admin

from models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published')
    search_fields = ('title', 'source')

admin.site.register(News, NewsAdmin)
