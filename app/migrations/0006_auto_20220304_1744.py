# Generated by Django 2.2 on 2022-03-04 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_league_ispublic'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='limit',
            field=models.FloatField(default=2000),
        ),
        migrations.AlterField(
            model_name='league',
            name='isPublic',
            field=models.BooleanField(default=True),
        ),
    ]