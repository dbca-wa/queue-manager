# Generated by Django 3.1.5 on 2022-10-13 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_site_queue', '0012_sitequeuemanagergroup_custom_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitequeuemanagergroup',
            name='custom_message',
            field=models.TextField(blank=True, max_length=400, null=True),
        ),
    ]