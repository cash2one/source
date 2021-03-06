# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.db.models import get_model
from django.db import transaction

from eloue.utils import cache_key, create_alternative_email
from django.core import exceptions
from parse_rest.connection import register
from parse_rest.installation import Push
from django.core.management import call_command


def post_save_answer(sender, instance, created, **kwargs):
    instance.question.save()


ELOUE_SITE_ID = 1
GOSPORT_SITE_ID = 13


@transaction.atomic
def __update_product_category(sender, instance, created, **kwargs):
    Product2Category = get_model('products', 'Product2Category')

    Product2Category.objects.filter(product=instance).delete()
    for site_id in settings.DEFAULT_SITES:
        category = instance.category.get_conformity(site_id)
        if category:
            Product2Category.objects.create(product=instance, category=category, site_id=site_id)
            instance.sites.add(site_id)
        else:
            instance.sites.remove(site_id)


def __reset_product_cache(sender, instance, created, **kwargs):
    cache.delete(cache_key('product:patron:row', instance.id))
    cache.delete(cache_key('product:breadcrumb', instance.pk))


def post_save_product(sender, instance, created, **kwargs):
    __reset_product_cache(
        sender=sender, instance=instance,
        created=created, **kwargs
    )
    __update_product_category(
        sender=sender, instance=instance,
        created=created, **kwargs
    )


def post_save_to_update_product(sender, instance, created, **kwargs):
    try:
        product = instance.product
        if product is not None:
            # Fixed issues with picture.json fixture when running tests:
            # it doesn't make sense to emit signal for None product
            __reset_product_cache(
                sender=product.__class__, instance=product,
                raw=False, created=False
            )
    except exceptions.ObjectDoesNotExist:
        pass


def post_save_to_batch_update_product(sender, instance, created, **kwargs):
    for product in instance.products.all():
        __reset_product_cache(
            sender=product.__class__, instance=product,
            raw=False, created=False
        )


def post_save_curiosity(sender, instance, created, **kwargs):
    cache.delete(cache_key('curiosities', Site.objects.get_current()))


def post_save_message(sender, instance, created, **kwargs):
    if not created:
        return

    # perform thread updates after creating a new message
    thread = instance.thread
    if thread:
        # update archive states
        if instance.sender == thread.sender:
            if thread.recipient_archived:
                thread.recipient_archived = False
        elif instance.sender == thread.recipient:
            if thread.sender_archived:
                thread.sender_archived = False
        # TODO: should we log or notify user somehow if message's sender is not a participant of the message thread?

        # update message thread to point to the created message
        thread.last_message = instance
        # FIXME: should we rally update 'last_offer'? I didn't find any use of it
        if instance.offer:
            thread.last_offer = instance

        thread.save()

    # perform parent message updates after creating a new message
    parent_msg = instance.parent_msg
    if parent_msg:
        parent_msg.replied_at = instance.sent_at
        parent_msg.save()


def new_message_email(sender, instance, created, **kwargs):
    """
    This function sends an email and is called via Django's signal framework.
    Optional arguments:
        ``template_name``: the template to use
        ``subject_prefix``: prefix for the email subject.
        ``default_protocol``: default protocol in site URL passed to template
    """
    if created and instance.recipient.email:
        context = {'message': instance}
        message = create_alternative_email(
            'django_messages/new_message', context, settings.DEFAULT_FROM_EMAIL, [instance.recipient.email])
        message.send()
        #Parse notification
        print instance.recipient.email
        print instance.recipient.device_token
        if instance.recipient.device_token:
            print "NOTIFICATION"
            register(settings.PARSE_APPLICATION_ID, settings.PARSE_REST_API_KEY)
            unread_count = instance.recipient.received_messages.filter(read_at=None).count()
            Push.alert({"alert": "Vous avez reçu un nouveau message", "type": "MSG_NEW", "user_id": instance.recipient.pk, "count": unread_count, "badge": unread_count, "sound": "default"}, where={"deviceToken": instance.recipient.device_token})


def post_save_property():
    call_command("configure_algolia", interactive=False)
    
