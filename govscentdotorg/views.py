from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Min, Max, Q
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from govscentdotorg.models import Bill
from govscentdotorg.models import BillTopic
from govscentdotorg.services.bill_html_generator import us_bill_text_to_html


BILL_TYPES = [
    ('HR', 'House Bill'),
    ('S', 'Senate Bill'),
    ('HJRES', 'House Joint Resolution'),
    ('SJRES', 'Senate Joint Resolution'),
    ('HRES', 'House Resolution'),
    ('SRES', 'Senate Resolution'),
    ('HCONRES', 'House Concurrent Resolution'),
    ('SCONRES', 'Senate Concurrent Resolution'),
]

ALLOWED_SORTS = {
    '-date': '-date',
    'date': 'date',
    '-score': '-on_topic_ranking',
    'score': 'on_topic_ranking',
    '-analyzed': '-last_analyzed_at',
}


def get_stats_cached():
    from govscentdotorg.services.cache_warmer import warm_index_stats
    result = cache.get('index_stats_v3')
    if not result:
        result = warm_index_stats()
    return result


def get_trending_topics_cached():
    from govscentdotorg.services.cache_warmer import warm_trending_topics
    result = cache.get('trending_topics_v1')
    if not result:
        result = warm_trending_topics()
    return result or []


def get_congress_sessions_cached():
    from govscentdotorg.services.cache_warmer import warm_congress_sessions
    result = cache.get('congress_sessions_v1')
    if not result:
        result = warm_congress_sessions()
    return result or []


def index(request):
    congress = request.GET.get('congress', '').strip()
    bill_type = request.GET.get('type', '').strip()
    score_min = request.GET.get('score_min', '').strip()
    score_max = request.GET.get('score_max', '').strip()
    sort = request.GET.get('sort', '-date').strip()
    page = request.GET.get('page', 1)

    qs = Bill.objects.filter(gov__exact="USA", last_analyzed_at__isnull=False)

    if congress:
        qs = qs.filter(gov_id__startswith=congress)
    if bill_type:
        qs = qs.filter(type__iexact=bill_type)
    if score_min:
        try:
            qs = qs.filter(on_topic_ranking__gte=int(score_min))
        except ValueError:
            pass
    if score_max:
        try:
            qs = qs.filter(on_topic_ranking__lte=int(score_max))
        except ValueError:
            pass

    order = ALLOWED_SORTS.get(sort, '-date')
    qs = qs.order_by(order).prefetch_related('topics')

    paginator = Paginator(qs, 24)
    paginated_bills = paginator.get_page(page)

    return render(request, 'index.html', {
        'paginated_bills': paginated_bills,
        'stats': get_stats_cached(),
        'trending_topics': get_trending_topics_cached(),
        'congress_sessions': get_congress_sessions_cached(),
        'bill_types': BILL_TYPES,
        'current_filters': {
            'congress': congress,
            'type': bill_type,
            'score_min': score_min,
            'score_max': score_max,
            'sort': sort,
        },
    })


def get_related_bills_cached(bill):
    cache_key = f'related_bills:{bill.gov}:{bill.gov_id}'
    result = cache.get(cache_key)
    if result is None:
        topic_ids = list(bill.topics.values_list('id', flat=True))
        if topic_ids:
            result = list(
                Bill.objects.filter(
                    topics__in=topic_ids,
                    last_analyzed_at__isnull=False
                ).exclude(
                    gov_id=bill.gov_id
                ).distinct().order_by('-date').only(
                    'gov_id', 'title', 'date', 'gov', 'on_topic_ranking', 'type', 'text_summary'
                )[:8]
            )
        else:
            result = []
        cache.set(cache_key, result, 3600)
    return result


def bill_page(request, gov, gov_id):
    # Check the rendered-HTML cache before loading the bill so we can skip
    # pulling the massive `text` column from Postgres on cache hits (which
    # are the common case for bot traffic).
    bill_html_cache_key = gov + gov_id
    force_refresh = request.GET.get('no_cache', '') == 'True'
    bill_html = None if force_refresh else cache.get(bill_html_cache_key)

    bill_qs = Bill.objects.filter(gov__exact=gov, gov_id__exact=gov_id).prefetch_related('topics')
    if bill_html is not None:
        bill_qs = bill_qs.defer(
            'text', 'last_analyze_response', 'final_analyze_response', 'last_analyze_error'
        )
    bill = bill_qs.first()
    if not bill:
        raise Http404

    if bill_html is None:
        bill_html = us_bill_text_to_html(bill.text)
        cache.set(bill_html_cache_key, bill_html, 3600)

    related_bills = get_related_bills_cached(bill)

    other_revisions = []
    if bill.gov_group_id:
        other_revisions = Bill.objects.filter(
            gov=gov, gov_group_id=bill.gov_group_id
        ).exclude(gov_id=gov_id).order_by('-date').only(
            'gov_id', 'title', 'date', 'gov'
        )

    return render(request, 'bill.html', {
        'bill': bill,
        'bill_html': bill_html,
        'related_bills': related_bills,
        'other_revisions': other_revisions,
    })


def topic_page(request, bill_topic_id: str, slug=''):
    bill_topic = BillTopic.objects.filter(id__exact=bill_topic_id).first()
    if not bill_topic:
        raise Http404

    sort = request.GET.get('sort', '-date').strip()
    page = request.GET.get('page', 1)

    order = ALLOWED_SORTS.get(sort, '-date')

    cache_key = f'bills-by-topic-v2:{bill_topic_id}:{sort}'
    qs = cache.get(cache_key)
    if qs is None or request.GET.get('no_cache', '') == 'True':
        qs = Bill.objects.filter(topics__in=[bill_topic]).order_by(order).only(
            'id', 'title', 'gov', 'gov_id', 'date', 'on_topic_ranking', 'text_summary', 'type'
        )
        cache.set(cache_key, qs, 3600)

    paginator = Paginator(qs, 20)
    paginated_bills = paginator.get_page(page)

    # Topic stats
    stats_key = f'topic-stats:{bill_topic_id}'
    topic_stats = cache.get(stats_key)
    if topic_stats is None:
        agg = Bill.objects.filter(
            topics__in=[bill_topic], on_topic_ranking__isnull=False
        ).aggregate(
            avg_score=Avg('on_topic_ranking'),
            total_count=Count('id'),
            high_count=Count('id', filter=Q(on_topic_ranking__gte=8)),
            mid_count=Count('id', filter=Q(on_topic_ranking__gte=4, on_topic_ranking__lt=8)),
            low_count=Count('id', filter=Q(on_topic_ranking__lt=4)),
        )
        topic_stats = {
            'avg_score': agg['avg_score'],
            'total_count': agg['total_count'],
            'high_count': agg['high_count'],
            'mid_count': agg['mid_count'],
            'low_count': agg['low_count'],
        }
        cache.set(stats_key, topic_stats, 3600)

    return render(request, 'topic.html', {
        'bill_topic': bill_topic,
        'paginated_bills': paginated_bills,
        'topic_stats': topic_stats,
        'current_sort': sort,
    })


def get_topic_search_query(request):
    if request.method == 'POST':
        return request.POST.get("searched")
    return request.GET.get("searched")


def get_topics_query_set(request, search_input: str | None):
    if search_input:
        search_vector = SearchVector('search_vector', config='english')
        search_query = SearchQuery(search_input)
        return BillTopic.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                bill_count=Count('related_bills'),
                avg_score=Avg('related_bills__on_topic_ranking')
        ).filter(search_vector=search_query, rank__gte=0.01).order_by('-bill_count')
    else:
        return BillTopic.objects.annotate(
            bill_count=Count('related_bills'),
            avg_score=Avg('related_bills__on_topic_ranking')
        ).order_by('-bill_count')


@cache_page(5 * 60)
@csrf_exempt
def topic_search_page(request):
    search_input = get_topic_search_query(request)
    page_number = request.POST.get('page')
    if page_number is None:
        page_number = request.GET.get('page')

    paginator = Paginator(get_topics_query_set(request, search_input), 48)
    paginated_data = paginator.get_page(page_number)

    popular_topics = None
    if not search_input:
        popular_topics = BillTopic.objects.annotate(
            bill_count=Count('related_bills'),
            avg_score=Avg('related_bills__on_topic_ranking')
        ).order_by('-bill_count')[:24]

    return render(request, 'topicSearch.html', {
        'searched': search_input,
        'paginated_data': paginated_data,
        'popular_topics': popular_topics,
    })


def bill_search_page(request):
    query = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)

    results = Bill.objects.none()
    if query:
        results = Bill.objects.filter(
            Q(title__icontains=query) | Q(gov_id__icontains=query),
            gov='USA',
            last_analyzed_at__isnull=False,
        ).prefetch_related('topics').order_by('-date')

    paginator = Paginator(results, 24)
    paginated_bills = paginator.get_page(page)

    return render(request, 'billSearch.html', {
        'query': query,
        'paginated_bills': paginated_bills,
    })


def congress_page(request, congress_number: int):
    bill_type = request.GET.get('type', '').strip()
    sort = request.GET.get('sort', '-date').strip()
    page = request.GET.get('page', 1)

    qs = Bill.objects.filter(
        gov='USA',
        gov_id__startswith=str(congress_number),
        last_analyzed_at__isnull=False
    ).prefetch_related('topics')

    if bill_type:
        qs = qs.filter(type__iexact=bill_type)

    order = ALLOWED_SORTS.get(sort, '-date')
    qs = qs.order_by(order)

    paginator = Paginator(qs, 24)
    paginated_bills = paginator.get_page(page)

    stats_key = f'congress-stats:{congress_number}'
    cached = cache.get(stats_key)
    if cached:
        congress_stats, date_range = cached
    else:
        all_bills = Bill.objects.filter(gov='USA', gov_id__startswith=str(congress_number))
        agg = all_bills.aggregate(
            total=Count('id'),
            analyzed=Count('id', filter=Q(last_analyzed_at__isnull=False)),
            avg_score=Avg('on_topic_ranking', filter=Q(on_topic_ranking__isnull=False)),
            earliest=Min('date'),
            latest=Max('date'),
        )
        congress_stats = {
            'total': agg['total'],
            'analyzed': agg['analyzed'],
            'avg_score': agg['avg_score'],
            'type_counts': list(all_bills.values('type').annotate(count=Count('id')).order_by('-count')),
        }
        date_range = {'earliest': agg['earliest'], 'latest': agg['latest']}
        cache.set(stats_key, (congress_stats, date_range), 3600)

    return render(request, 'congress.html', {
        'congress_number': congress_number,
        'paginated_bills': paginated_bills,
        'congress_stats': congress_stats,
        'date_range': date_range,
        'bill_types': BILL_TYPES,
        'current_filters': {
            'type': bill_type,
            'sort': sort,
        },
    })


def stats_page(request):
    from govscentdotorg.services.cache_warmer import warm_congress_breakdown
    breakdown = cache.get('stats_congress_breakdown')
    if not breakdown:
        breakdown = warm_congress_breakdown()
    return render(request, 'stats.html', {
        'stats': get_stats_cached(),
        'congress_breakdown': breakdown or [],
    })
