# Generated by Django 4.1.7 on 2023-05-19 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('govscentdotorg', '0022_billsection_text_end_billsection_text_start'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billsection',
            name='text',
        ),
        migrations.AlterField(
            model_name='billsection',
            name='text_end',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='billsection',
            name='text_start',
            field=models.PositiveIntegerField(),
        ),
    ]