import re

from django import template

register = template.Library()

# Regex to parse gov_id like "118hr123ih" into (congress, type, number, status)
GOV_ID_RE = re.compile(r'^(\d+)([a-z]+?)(\d+)([a-z]+)$', re.IGNORECASE)

TYPE_FULL_NAMES = {
    'hr': 'House Bill',
    's': 'Senate Bill',
    'hjres': 'House Joint Resolution',
    'sjres': 'Senate Joint Resolution',
    'hres': 'House Resolution',
    'sres': 'Senate Resolution',
    'hconres': 'House Concurrent Resolution',
    'sconres': 'Senate Concurrent Resolution',
}

# Congress.gov URL path segments
TYPE_URL_SEGMENTS = {
    'hr': 'house-bill',
    's': 'senate-bill',
    'hjres': 'house-joint-resolution',
    'sjres': 'senate-joint-resolution',
    'hres': 'house-resolution',
    'sres': 'senate-resolution',
    'hconres': 'house-concurrent-resolution',
    'sconres': 'senate-concurrent-resolution',
}

STATUS_NAMES = {
    'ih': 'Introduced in House',
    'is': 'Introduced in Senate',
    'rh': 'Reported in House',
    'rs': 'Reported in Senate',
    'rds': 'Received in Senate',
    'rfs': 'Referred in Senate',
    'rfh': 'Referred in House',
    'eh': 'Engrossed in House',
    'es': 'Engrossed in Senate',
    'enr': 'Enrolled',
    'eas': 'Engrossed Amendment Senate',
    'eah': 'Engrossed Amendment House',
    'pcs': 'Placed on Calendar Senate',
    'pch': 'Placed on Calendar House',
    'pp': 'Public Print',
    'cps': 'Considered and Passed Senate',
    'cph': 'Considered and Passed House',
    'ats': 'Agreed to Senate',
    'ath': 'Agreed to House',
    'iph': 'Indefinitely Postponed House',
    'ips': 'Indefinitely Postponed Senate',
    'lth': 'Laid on Table House',
    'lts': 'Laid on Table Senate',
    'oph': 'Ordered to be Printed House',
    'ops': 'Ordered to be Printed Senate',
    'hdh': 'Held at Desk House',
    'hds': 'Held at Desk Senate',
    'fah': 'Failed Amendment House',
    'fas': 'Failed Amendment Senate',
    'sc': 'Sundry Correspondence',
    'cdh': 'Committee Discharged House',
    'cds': 'Committee Discharged Senate',
    'rah': 'Referred w/Amendments House',
    'ras': 'Referred w/Amendments Senate',
    'rch': 'Reference Change House',
    'rcs': 'Reference Change Senate',
    'ash': 'Additional Sponsors House',
    'renr': 'Re-enrolled',
    'reah': 'Re-engrossed Amendment House',
}

ORDINAL_SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}


def _parse_gov_id(gov_id):
    if not gov_id:
        return None
    m = GOV_ID_RE.match(str(gov_id).lower())
    if not m:
        return None
    return {
        'congress': m.group(1),
        'type': m.group(2),
        'number': m.group(3),
        'status': m.group(4),
    }


def _ordinal(n):
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ORDINAL_SUFFIXES.get(n % 10, 'th')
    return f'{n}{suffix}'


@register.simple_tag
def congress_number(gov_id):
    parsed = _parse_gov_id(gov_id)
    return parsed['congress'] if parsed else ''


@register.simple_tag
def congress_ordinal(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return ''
    return _ordinal(parsed['congress'])


@register.simple_tag
def bill_type_full(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return ''
    return TYPE_FULL_NAMES.get(parsed['type'], parsed['type'].upper())


@register.simple_tag
def bill_type_short(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return ''
    return parsed['type'].upper()


@register.simple_tag
def bill_number(gov_id):
    parsed = _parse_gov_id(gov_id)
    return parsed['number'] if parsed else ''


@register.simple_tag
def bill_status_code(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return ''
    return STATUS_NAMES.get(parsed['status'], parsed['status'].upper())


@register.simple_tag
def congress_gov_url(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return '#'
    segment = TYPE_URL_SEGMENTS.get(parsed['type'])
    if not segment:
        return '#'
    congress = parsed['congress']
    ordinal = _ordinal(congress)
    return f'https://www.congress.gov/bill/{ordinal}-congress/{segment}/{parsed["number"]}'


@register.simple_tag
def bill_chamber(gov_id):
    parsed = _parse_gov_id(gov_id)
    if not parsed:
        return ''
    return 'House' if parsed['type'].startswith('h') else 'Senate'


@register.simple_tag
def score_color(score):
    if score is None:
        return ''
    try:
        s = int(score)
    except (ValueError, TypeError):
        return ''
    if s >= 8:
        return 'score-high'
    elif s >= 4:
        return 'score-mid'
    return 'score-low'


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Replace or add query parameters while preserving existing ones."""
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is None:
            query.pop(k, None)
        else:
            query[k] = v
    return query.urlencode()
