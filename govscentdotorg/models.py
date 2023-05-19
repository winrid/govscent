import datetime

from admin_numeric_filter.admin import NumericFilterModelAdmin, RangeNumericFilter
from django.contrib.admin import EmptyFieldListFilter
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin, ExportActionModelAdmin
from django.contrib.postgres.indexes import GinIndex
from django.core.cache import cache


class BillTopic(models.Model):
    name = models.TextField(unique=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return self.name

    def get_bill_count_cached(self) -> int:
        """
        Note - this will hit disk with current cache config, but usually still faster than scanning index which may hit disk anyway.
        Especially for topics that have many bills.
        """
        cache_key = "topic_bill_count:" + str(self.id)
        count = cache.get(cache_key)
        if count is None:
            count = self.related_bills.count()
            cache.set(cache_key, count, 86400)  # Cache for 24 hours.
        return count


class BillSmell(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])
    description = models.TextField()

    def __str__(self):
        return self.name


class BillSection(models.Model):
    text_start = models.PositiveIntegerField(blank=True, null=True)  # TODO NOT NULL
    text_end = models.PositiveIntegerField(blank=True, null=True)  # TODO NOT NULL
    last_analyze_model = models.CharField(max_length=100, default="gpt-3-turbo", null=True)
    last_analyze_error = models.TextField(default=None, blank=True, null=True)
    last_analyze_response = models.TextField(default=None, blank=True, null=True)

    def get_text(self, bill_text: str):
        if self.text_start is not None and self.text_end is not None:
            return " ".join(bill_text.split(" ")[self.text_start:self.text_end])
        return None


class Bill(models.Model):
    gov = models.CharField(max_length=8, verbose_name="Government")
    # For the USA: congress + bill type + bill #
    gov_id = models.CharField(max_length=1000, verbose_name="Bill Identifier",
                              help_text="Each revision of bill has its own gov_id.")
    gov_group_id = models.CharField(max_length=1000, verbose_name="Bill Group Identifier",
                                    help_text="Can be used to group a bill across many versions.", default=None,
                                    blank=True, null=True)
    is_latest_revision = models.BooleanField(default=False)
    title = models.TextField()
    type = models.CharField(max_length=50)
    source_file_path = models.TextField(blank=True, null=True)
    text = models.TextField(default="")
    date = models.DateField()
    last_analyzed_at = models.DateTimeField(default=None, blank=True, null=True)
    last_analyze_error = models.TextField(default=None, blank=True, null=True)
    last_analyze_response = models.TextField(default=None, blank=True, null=True)
    final_analyze_response = models.TextField(default=None, blank=True, null=True)
    last_analyze_model = models.CharField(max_length=100, default="gpt-3.5-turbo", null=True)
    bill_sections = models.ManyToManyField(BillSection, related_name="sections", blank=True)

    topics = models.ManyToManyField(BillTopic, related_name="related_bills", blank=True)
    text_summary = models.TextField(default=None, blank=True, null=True)
    smells = models.ManyToManyField(BillSmell, blank=True)
    on_topic_ranking = models.PositiveSmallIntegerField(default=None, blank=True, null=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(100)
    ])
    on_topic_reasoning = models.TextField(default=None, blank=True, null=True)
    smelliness = models.IntegerField(default=None, blank=True, null=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(100),
    ])

    class Meta:
        # if gov_id ends up not being unique enough, we could add date too, it'll just make the index bigger...
        unique_together = ('gov', 'gov_id')
        indexes = [
            models.Index(fields=['gov_id']),
            models.Index(fields=['date']),
            models.Index(fields=['on_topic_ranking']),
            models.Index(fields=['gov', 'date']),
            models.Index(fields=['last_analyzed_at']),
            models.Index(fields=['last_analyzed_at', 'is_latest_revision']),
            models.Index(fields=['gov', 'gov_group_id']),
        ]

    def __str__(self):
        return self.title


class BillTopicAdmin(ImportExportModelAdmin, ExportActionModelAdmin):
    list_display = ('name', 'bill_count')
    readonly_fields = ('bill_links',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _bill_count=Count("related_bills", distinct=True),
        )
        return queryset

    def bill_count(self, obj):
        return obj._bill_count

    bill_count.short_description = "# of Bills"
    bill_count.admin_order_field = '_bill_count'

    def bill_links(self, obj):
        html = '<ol>'
        bills = Bill.objects.filter(topics__in=[obj]).only('id', 'title')
        for bill in bills:
            html += f'<li><a href="{reverse("admin:govscentdotorg_bill_change", args=(bill.pk,))}">{bill.title}</a></li>'
        html += '</ol>'
        return mark_safe(html)

    bill_links.short_description = 'Bills'


class BillAdmin(NumericFilterModelAdmin, ImportExportModelAdmin, ExportActionModelAdmin):
    date_hierarchy = 'date'
    list_display = ('title', 'on_topic_ranking', 'date')
    list_filter = (
    'is_latest_revision', ('last_analyze_error', EmptyFieldListFilter), ('on_topic_ranking', RangeNumericFilter))
    search_fields = ('gov_id',)
    raw_id_fields = ('topics', 'bill_sections')
    readonly_fields = ('section_links',)

    def section_links(self, obj):
        html = '<ol>'
        sections = BillSection.objects.filter(sections__in=[obj]).only('id')
        for section in sections:
            html += f'<li><a href="{reverse("admin:govscentdotorg_billsection_change", args=(section.pk,))}">{section.id}</a></li>'
        html += '</ol>'
        return mark_safe(html)

    section_links.short_description = 'Sections'


class BillSectionAdmin(ImportExportModelAdmin, ExportActionModelAdmin):
    list_display = ('id', 'last_analyze_error')
    readonly_fields = ('section_text',)

    def section_text(self, obj):
        bill = Bill.objects.filter(bill_sections__in=[obj]).only('text').first()
        if not Bill:
            return mark_safe('Bill Missing.')
        html = f'<textarea readonly>{obj.get_text(bill.text)}</textarea>'
        return mark_safe(html)

    section_text.short_description = 'Section Text'
