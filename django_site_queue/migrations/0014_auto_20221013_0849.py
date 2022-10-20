# Generated by Django 3.1.5 on 2022-10-13 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_site_queue', '0013_auto_20221013_0428'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitequeuemanagergroup',
            name='more_info_link',
            field=models.CharField(blank=True, help_text='More info link on public waiting queue', max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='sitequeuemanagergroup',
            name='queue_name',
            field=models.CharField(blank=True, help_text='Queue header name to appear on public waiting queue. ', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='sitequeuemanagergroup',
            name='custom_message',
            field=models.TextField(blank=True, help_text='Short message to explain the reason for the waiting queue', max_length=400, null=True),
        ),
    ]