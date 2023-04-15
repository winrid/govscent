import json

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from govscentdotorg.models import Bill
from govscentdotorg.models import BillTopic
from govscentdotorg.services.bill_html_generator import us_bill_text_to_html


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
        average_smelliness_by_year = Bill.objects \
            .annotate(year=TruncMonth('date')) \
            .values('year') \
            .annotate(score=Avg('on_topic_ranking')) \
            .order_by('year') \
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

    # HTML generation lazily is nice because storage space is much lower and pure text compresses well.
    # Also, this is much quicker to iterate on when needed.
    bill_html_cache_key = gov + gov_id
    bill_html = cache.get(bill_html_cache_key)
    if bill_html is None or request.GET.get('no_cache', '') == 'True':
        bill_html = us_bill_text_to_html(bill.text)
        cache.set(bill_html_cache_key, bill_html, 3600)  # Cache for an hour.
    return render(request, 'bill.html', {
        'bill': bill,
        'bill_html': bill_html
    })


def topic_page(request, bill_topic_id: str, slug):
    bill_topic = BillTopic.objects.filter(id__exact=bill_topic_id).first()
    if not bill_topic:
        raise Http404
    # HTML generation lazily is nice because storage space is much lower and pure text compresses well.
    # Also, this is much quicker to iterate on when needed.

    cache_key = f'bills-by-topic:{bill_topic_id}'
    bills = cache.get(cache_key)
    if bills is None or request.GET.get('no_cache', '') == 'True':
        bills = Bill.objects.filter(topics__in=[bill_topic]).order_by('-date').only('id', 'title', 'gov', 'gov_id')
        cache.set(cache_key, bills, 3600)  # Cache for an hour.
    return render(request, 'topic.html', {
        'bill_topic': bill_topic,
        'bills': bills
    })


def get_topic_search_query(request):
    if request.method == 'POST':
        return request.POST.get("searched")
    return request.GET.get("searched")


def get_topics_query_set(request, search_input: str | None):
    if search_input:
        search_vector = SearchVector('search_vector', config='english')
        search_query = SearchQuery(search_input)
        # TODO custom sort direction (rank, # of bills, etc)
        return BillTopic.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                bill_count=Count('related_bills')
        )\
            .filter(search_vector=search_query, rank__gte=0.01)\
            .order_by('-bill_count')
    else:
        return BillTopic.objects.annotate(
            bill_count=Count('related_bills')
        ).order_by('-bill_count')


@cache_page(5 * 15)  # Cache for 5 minutes.
def topic_search_page(request):
    search_input = get_topic_search_query(request)
    page_number = request.POST.get('page')
    if page_number is None:
        page_number = request.GET.get('page')

    paginator = Paginator(get_topics_query_set(request, search_input), 100)
    paginated_data = paginator.get_page(page_number)

    return render(request, 'topicSearch.html', {
        'searched': search_input,
        'paginated_data': paginated_data
    })

