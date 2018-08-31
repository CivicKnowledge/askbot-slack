import json
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from askbot_slack import conf #register slack settings
from askbot.conf import settings as askbot_settings
from askbot.models import Post


def get_url(model_instance):
    """
    Returns the URL for the model instance.  Dependent on Site Domain name being set.
    """
    return "{}{}".format(askbot_settings.SLACK_BASE_URL, model_instance.get_absolute_url())



@receiver(post_save, sender=Post)
def notify_post_created(sender, instance, created, raw, using, **kwargs):
    """
    Post message when Askbot Post is created.  A Post includes Questions, Comments and Answers.
    """
    if created and askbot_settings.SLACK_ENABLED:
        
        from django.core import serializers

        # assuming obj is a model instance
        serialized_obj = serializers.serialize('json', [ instance, instance.thread, instance.author])
        
        
        title = instance.thread.title
        thread_id = instance.thread_id
        object_id = instance_id
     
        
        payload = {
        	"text": None,
            "username": askbot_settings.SLACK_USERNAME,
            "channel": askbot_settings.SLACK_CHANNEL,
            
            "attachments": [
                {
                    "fallback": instance.thread.title,
                    "color": "#36a64f",
                    "author_name": instance.author.username,
                    "author_link": get_url(instance.author),
                    "author_icon": "https:"+instance.author.get_avatar_url(120),
                    "title": instance.thread.title,
                    "title_link": get_url(instance),
                    "text": instance.text,
                    #"image_url": "http://my-website.com/path/to/image.jpg",
                    #"thumb_url": "http://example.com/path/to/thumb.png",
                    "footer": "Insights",
                    "footer_icon": "http://www.civicknowledge.com/wp-content/uploads/sites/3/2018/08/CivicKnowledge_icon_144.png",
                }
            ]
        }

        if instance.is_question():
            payload['text'] = _('New Question') 
            payload['ts'] = thread_id
        elif instance.is_answer():
            payload['text'] = _('New Answer') 
            payload['ts'] = object_id
            payload['thread_ts'] = thread_id
        elif instance.is_comment():
            payload['text'] = _('New Comment') 
            payload['ts'] = object_id
            payload['thread_ts'] = thread_id
            
            
        requests.post(askbot_settings.SLACK_WEBHOOK_URL, data=json.dumps(payload))


class SlackMiddleware(object):
    """
    A NO-OP middleware class to ensure our receiver gets registered early on.
    From the django 1.5 docs on signals: 'make sure that the module it's in gets imported early on so that the signal
    handling gets registered before any signals need to be sent'.  Registering as a no-op middleware class ensures that
    this is 'imported early on'.  In later versions of django we can use the App#register method.
    """
    pass
