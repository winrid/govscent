# Generated by Django 4.1.7 on 2023-03-26 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('govscentdotorg', '0014_bill_source_file_path'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='bill',
            index=models.Index(fields=['on_topic_ranking'], name='govscentdot_on_topi_32544f_idx'),
        ),
    ]
