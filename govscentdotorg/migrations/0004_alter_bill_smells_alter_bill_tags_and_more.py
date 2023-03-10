# Generated by Django 4.1.7 on 2023-02-27 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('govscentdotorg', '0003_alter_bill_smelliness_alter_bill_smells_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='smells',
            field=models.ManyToManyField(to='govscentdotorg.billsmell'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='tags',
            field=models.ManyToManyField(to='govscentdotorg.billtags'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='text_topics',
            field=models.ManyToManyField(related_name='text_topics', to='govscentdotorg.billtopic'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='title_topics',
            field=models.ManyToManyField(related_name='title_topics', to='govscentdotorg.billtopic'),
        ),
    ]
