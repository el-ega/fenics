from django.conf import settings

from ega.constants import DEFAULT_TOURNAMENT
from ega.models import Tournament


def disqus_shortname(request):
    """Adds disqus shortname setting as variable to the context."""
    return {'DISQUS_SHORTNAME': settings.DISQUS_SHORTNAME}


def available_tournaments(request):
    """Adds available tournaments information as variable to the context."""
    enabled = Tournament.objects.filter(published=True, finished=False)
    available = {t.slug: t for t in enabled}
    current_slug = request.session.get('tournament', DEFAULT_TOURNAMENT)
    current = available.get(current_slug, available.get(DEFAULT_TOURNAMENT))
    return {'available_tournaments': available, 'current_tournament': current}
