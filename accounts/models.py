import urllib2

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.db import models
from django.template.defaultfilters import slugify

from social_auth.backends.facebook import FacebookBackend
from social_auth.backends.twitter import TwitterBackend
from social_auth.signals import pre_update


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    avatar = models.ImageField(upload_to='accounts', blank=True,
                               default='accounts/default_avatar.jpg')
    favorite_club = models.ForeignKey('game.Team', blank=True, null=True)

    def __unicode__(self):
        return "Profile: %s" % self.user


def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        
post_save.connect(create_profile, sender=User, dispatch_uid="create-profile")


def set_user_avatar(sender, user, response, details, **kwargs):
    """Update avatar in user profile."""
    result = False

    if "id" in response:
        try:
            url = None
            if sender == FacebookBackend:
                url = "http://graph.facebook.com/%s/picture?type=large" \
                            % response["id"]
            elif sender == TwitterBackend:
                url = response["profile_image_url"]

            if url:
                profile = user.get_profile()

                data = urllib2.urlopen(url)
                profile.avatar.save(slugify(user.username + " social") + '.jpg',
                                    ContentFile(data.read()))
                profile.save()

        except urllib2.HTTPError:
            pass

        result = True

    return result


pre_update.connect(set_user_avatar, sender=None,
                   dispatch_uid="set-profile-avatar")
