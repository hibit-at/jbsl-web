# Generated by Django 2.2 on 2022-03-04 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_player_indiscord'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='isPublic',
            field=models.BooleanField(default=False),
        ),
    ]