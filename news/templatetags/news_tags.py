from django import template

from news.models import News


register = template.Library()


@register.inclusion_tag('news/latest_news.html')
def latest_news(source, latest=3):
    news = News.objects.filter(source=source).order_by('-published')[:latest]
    return {'news_items': news}
