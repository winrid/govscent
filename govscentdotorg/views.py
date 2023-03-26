from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render

from govscentdotorg.models import Bill


def get_index_bills_cached():
    index_bills = cache.get('index_bills')
    if not index_bills:
        index_bills = Bill.objects.filter(gov__exact="USA", last_analyzed_at__isnull=False).order_by('-date')[:50]
        cache.set('index_bills', index_bills)
    return index_bills


def index(request):
    return render(request, 'index.html', {
        'recent_bills': get_index_bills_cached()
    })


def bill_page(request, gov, gov_id):
    bill = Bill.objects.filter(gov__exact=gov, gov_id__exact=gov_id).first()
    if not bill:
        raise Http404
    return render(request, 'bill.html', {
        'bill': bill
    })
