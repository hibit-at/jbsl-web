# Generated by Django 3.2.18 on 2023-06-17 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0049_song_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='bid',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='lid',
            field=models.CharField(blank=True, default='', max_length=10, null=True),
        ),
    ]
