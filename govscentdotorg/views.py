from django.shortcuts import render

from govscentdotorg.models import Bill


def index(request):
    recent_bills = Bill.objects.filter(gov__exact="USA").order_by('-date')[:50]
    return render(request, 'index.html', {
        'recent_bills': recent_bills
    })


def bill_page(request, gov, bill_id):
    bill = Bill.objects.filter(gov__exact=gov, bill_id=bill_id).first()
    return render(request, 'bill.html', {
        'bill': bill
    })
