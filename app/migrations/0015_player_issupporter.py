# Generated by Django 2.2 on 2022-04-03 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20220316_2007'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='isSupporter',
            field=models.BooleanField(default=False),
        ),
    ]