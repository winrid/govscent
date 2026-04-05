import json
from datetime import timedelta

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, Func, CharField, Q, Min, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone

from govscentdotorg.models import Bill, BillTopic


def warm_all_caches():
    print("Warming index stats...")
    warm_index_stats()
    print("Warming trending topics...")
    warm_trending_topics()
    print("Warming congress sessions...")
    warm_congress_sessions()
    print("Warming congress breakdown...")
    warm_congress_breakdown()
    print("All caches warmed.")


def warm_index_stats():
    average_score_by_month = Bill.objects \
        .filter(on_topic_ranking__isnull=False) \
        .annotate(year=TruncMonth('date')) \
        .values('year') \
        .annotate(score=Avg('on_topic_ranking')) \
        .order_by('year') \
        .values('year', 'score')

    average_score_by_month_json = json.dumps(list(average_score_by_month), cls=DjangoJSONEncoder)

    index_stats = {
        'count_bills': Bill.objects.count(),
        'count_bills_analyzed': Bill.objects.filter(last_analyzed_at__isnull=False).count(),
        'average_score_by_month_json': average_score_by_month_json,
    }
    cache.set('index_stats_v3', index_stats, 86400)
    return index_stats


def warm_trending_topics():
    cutoff = timezone.now() - timedelta(days=90)
    result = list(
        BillTopic.objects.filter(
            related_bills__last_analyzed_at__gte=cutoff
        ).annotate(
            recent_count=Count('related_bills', distinct=True)
        ).order_by('-recent_count')[:12]
    )
    cache.set('trending_topics_v1', result, 86400)
    return result


def warm_congress_sessions():
    rows = Bill.objects.filter(gov='USA').annotate(
        congress=Func(
            'gov_id', function='SUBSTRING',
            template="%(function)s(%(expressions)s FROM '^[0-9]+')",
            output_field=CharField()
        )
    ).values_list('congress', flat=True).distinct()
    result = sorted({int(c) for c in rows if c}, reverse=True)
    cache.set('congress_sessions_v1', result, 86400)
    return result


def warm_congress_breakdown():
    rows = Bill.objects.filter(gov='USA').annotate(
        congress=Func(
            'gov_id', function='SUBSTRING',
            template="%(function)s(%(expressions)s FROM '^[0-9]+')",
            output_field=CharField()
        )
    ).values('congress').annotate(
        total=Count('id'),
        analyzed=Count('id', filter=Q(last_analyzed_at__isnull=False)),
        avg_score=Avg('on_topic_ranking', filter=Q(on_topic_ranking__isnull=False)),
    ).order_by('-congress')
    result = [r for r in rows if r['congress']]
    cache.set('stats_congress_breakdown', result, 86400)
    return result
