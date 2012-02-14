from django import template

from news.models import News


register = template.Library()


@register.inclusion_tag('news/latest_news.html')
def latest_news(latest=3):
    news = News.objects.all().order_by('-published')[:latest]
    return {'news_items': news}
