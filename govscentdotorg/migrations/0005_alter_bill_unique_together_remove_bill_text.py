# Generated by Django 4.1.7 on 2023-02-27 00:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('govscentdotorg', '0004_alter_bill_smells_alter_bill_tags_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='bill',
            unique_together={('gov', 'gov_id')},
        ),
        migrations.RemoveField(
            model_name='bill',
            name='text',
        ),
    ]