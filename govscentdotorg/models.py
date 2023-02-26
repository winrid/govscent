import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class BillTopic(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])


class BillSmell(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])
    description = models.TextField()


class Bill(models.Model):
    # For the USA: congress + bill type + bill #
    gov_id = models.CharField(max_length=1000)
    title = models.TextField()
    text = models.TextField()
    type = models.CharField(max_length=50)
    html = models.TextField()
    date = models.DateField()
    last_analyzed_at = models.DateTimeField(default=datetime.datetime)
    title_topics = models.ManyToManyField(BillTopic, related_name="title_topics")
    text_topics = models.ManyToManyField(BillTopic, related_name="text_topics")
    smells = models.ManyToManyField(BillSmell)
    smelliness = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])

    class Meta:
        indexes = [
            models.Index(fields=['gov_id']),
            models.Index(fields=['date']),
            models.Index(fields=['last_analyzed_at']),
        ]

