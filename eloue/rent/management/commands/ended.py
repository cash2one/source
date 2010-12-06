# -*- coding: utf-8 -*-
import logbook

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

log = logbook.Logger('eloue.rent.ended')


class Command(BaseCommand):
    help = "Find ended rentals and move them to ENDED state"
    
    def handle(self, *args, **options):
        """Find ending rent and move them as ENDED."""
        from eloue.rent.models import Booking
        log.info('Starting hourly ender mover process')
        dtime = datetime.now() + timedelta(hours=1)
        for booking in Booking.objects.ongoing().filter(ended_at__contains=' %02d' % dtime.hour,
            ended_at__day=dtime.day, ended_at__month=dtime.month,
            ended_at__year=dtime.year):
            booking.state = Booking.STATE.ENDED
            booking.send_ended_email()
            booking.save()
        log.info('Finished hourly ender mover process')
    
