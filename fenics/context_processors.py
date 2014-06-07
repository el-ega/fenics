from django.conf import settings


def disqus_shortname(request):
    """Adds disqus shortname setting as variable to the context."""
    return {'DISQUS_SHORTNAME': settings.DISQUS_SHORTNAME}
