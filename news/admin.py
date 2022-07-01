from django.contrib import admin

from news.models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published')
    search_fields = ('title', 'source')


admin.site.register(News, NewsAdmin)
