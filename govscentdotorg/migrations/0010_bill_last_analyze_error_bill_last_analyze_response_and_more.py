# Generated by Django 4.1.7 on 2023-03-19 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('govscentdotorg', '0009_billtopic_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='last_analyze_error',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='last_analyze_response',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='text_summary',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]