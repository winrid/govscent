from django.core.cache import cache
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


def bill_page(request, gov, bill_id):
    bill = Bill.objects.filter(gov__exact=gov, bill_id=bill_id).first()
    return render(request, 'bill.html', {
        'bill': bill
    })
