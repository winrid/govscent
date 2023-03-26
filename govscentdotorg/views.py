import json

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.shortcuts import render

from govscentdotorg.models import Bill


def get_index_bills_cached() -> [Bill]:
    index_bills = cache.get('index_bills')
    if not index_bills:
        index_bills = Bill.objects.filter(gov__exact="USA", last_analyzed_at__isnull=False).order_by('-date')[:50]
        cache.set('index_bills', index_bills)
    return index_bills


def get_stats_cached() -> object:
    key = 'index_stats_v2'
    index_stats = cache.get(key)
    if not index_stats:
        average_smelliness_by_year = Bill.objects\
            .annotate(year=TruncMonth('date'))\
            .values('year')\
            .annotate(score=Avg('on_topic_ranking'))\
            .order_by('year')\
            .values('year', 'score')

        average_smelliness_by_year_json = json.dumps(list(average_smelliness_by_year), cls=DjangoJSONEncoder)

        index_stats = {
            'count_bills': Bill.objects.count(),
            'count_bills_analyzed': Bill.objects.filter(on_topic_ranking__isnull=False).count(),
            'average_smelliness_by_year_json': average_smelliness_by_year_json
        }
    cache.set(key, index_stats)

    return index_stats


def index(request):
    return render(request, 'index.html', {
        'recent_bills': get_index_bills_cached(),
        'stats': get_stats_cached(),
    })


def bill_page(request, gov, gov_id):
    bill = Bill.objects.filter(gov__exact=gov, gov_id__exact=gov_id).first()
    if not bill:
        raise Http404
    return render(request, 'bill.html', {
        'bill': bill
    })
