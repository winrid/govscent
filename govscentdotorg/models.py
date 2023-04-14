import datetime

from admin_numeric_filter.admin import NumericFilterModelAdmin, RangeNumericFilter
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin, ExportActionModelAdmin


class BillTopic(models.Model):
    name = models.TextField(unique=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return self.name


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
    text = models.TextField()
    last_analyze_model = models.CharField(max_length=100, default="gpt-3-turbo", null=True)
    last_analyze_error = models.TextField(default=None, blank=True, null=True)
    last_analyze_response = models.TextField(default=None, blank=True, null=True)


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
    last_analyze_model = models.CharField(max_length=100, default="gpt-3-turbo", null=True)
    bill_sections = models.ManyToManyField(BillSection, related_name="sections")

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
    list_filter = ('is_latest_revision', ('on_topic_ranking', RangeNumericFilter))
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
