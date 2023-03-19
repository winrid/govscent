import datetime

from django.contrib import admin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe


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


class Bill(models.Model):
    gov = models.CharField(max_length=8, verbose_name="Government")
    # For the USA: congress + bill type + bill #
    gov_id = models.CharField(max_length=1000, verbose_name="Bill Identifier", help_text="Each revision of bill has its own gov_id.")
    gov_group_id = models.CharField(max_length=1000, verbose_name="Bill Group Identifier", help_text="Can be used to group a bill across many versions.", default=None, blank=True, null=True)
    is_latest_revision = models.BooleanField(default=False)
    title = models.TextField()
    type = models.CharField(max_length=50)
    text = models.TextField(default="")
    html = models.TextField(default="")
    date = models.DateField()
    last_analyzed_at = models.DateTimeField(default=None, null=True)
    last_analyze_error = models.TextField(default=None, blank=True, null=True)
    last_analyze_response = models.TextField(default=None, blank=True, null=True)

    topics = models.ManyToManyField(BillTopic, related_name="topics")
    text_summary = models.TextField(default=None, blank=True, null=True)
    smells = models.ManyToManyField(BillSmell)
    on_topic_ranking = models.PositiveSmallIntegerField(default=None, null=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(100)
    ])
    on_topic_reasoning = models.TextField(default=None, blank=True, null=True)
    smelliness = models.IntegerField(default=None, null=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(100),
    ])

    class Meta:
        # if gov_id ends up not being unique enough, we could add date too, it'll just make the index bigger...
        unique_together = ('gov', 'gov_id')
        indexes = [
            models.Index(fields=['gov_id']),
            models.Index(fields=['date']),
            models.Index(fields=['last_analyzed_at']),
            models.Index(fields=['last_analyzed_at', 'is_latest_revision']),
            models.Index(fields=['gov', 'gov_group_id']),
        ]

    def __str__(self):
        return self.title


class BillTopicAdmin(admin.ModelAdmin):
    readonly_fields = ('bill_links',)

    def bill_links(self, obj):
        html = '<ol>'
        bills = Bill.objects.filter(topics__in=[obj]).only('id', 'title')
        for bill in bills:
            html += f'<li><a href="{reverse("admin:govscentdotorg_bill_change", args=(bill.pk,))}">{bill.title}</a></li>'
        html += '</ol>'
        return mark_safe(html)
    bill_links.short_description = 'Bills'


class BillAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('title', 'date')
    list_filter = ('is_latest_revision', 'on_topic_ranking')
    search_fields = ('gov_id',)
