import datetime

from django.contrib import admin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class BillTopic(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])

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

class BillTags(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    sort_priority = models.IntegerField()

    def __str__(self):
        return self.name

class Bill(models.Model):
    gov = models.CharField(max_length=8, verbose_name="Government")
    # For the USA: congress + bill type + bill #
    gov_id = models.CharField(max_length=1000, verbose_name="Bill's Government Identifier")
    title = models.TextField()
    type = models.CharField(max_length=50)
    # For now, we just store raw bill HTML. We don't do parsing often, so in the interest of space, we store only one version (the HTML)
    # and extract the text when we need to.
    html = models.TextField()
    date = models.DateField()
    last_analyzed_at = models.DateTimeField(default=None, null=True)

    # There are a lot of relations here, which might be concerning. However, consistency is more important, as the data volume is low.
    # Caching and projections will be used to ensure performance stays okay.
    title_topics = models.ManyToManyField(BillTopic, related_name="title_topics")
    text_topics = models.ManyToManyField(BillTopic, related_name="text_topics")
    smells = models.ManyToManyField(BillSmell)
    smelliness = models.IntegerField(default=None, null=True, validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])
    tags = models.ManyToManyField(BillTags)

    class Meta:
        # if gov_id ends up not being unique enough, we could add date too, it'll just make the index bigger...
        unique_together=('gov', 'gov_id')
        indexes = [
            models.Index(fields=['gov_id']),
            models.Index(fields=['date']),
            models.Index(fields=['last_analyzed_at']),
        ]

    def __str__(self):
        return self.title

class BillAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('title', 'date')
