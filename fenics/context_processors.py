from django.conf import settings

from ega.models import Tournament


def disqus_shortname(request):
    """Adds disqus shortname setting as variable to the context."""
    return {'DISQUS_SHORTNAME': settings.DISQUS_SHORTNAME}


def available_tournaments(request):
    """Adds available tournaments information as variable to the context."""
    available = Tournament.objects.filter(
        published=True, finished=False
    ).order_by('name')
    return {'available_tournaments': available}
