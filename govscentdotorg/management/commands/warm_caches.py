from django.core.management.base import BaseCommand

from govscentdotorg.services.cache_warmer import warm_all_caches


class Command(BaseCommand):
    help = 'Pre-compute and cache expensive homepage data (stats, trending topics, congress sessions)'

    def handle(self, *args, **options):
        warm_all_caches()
