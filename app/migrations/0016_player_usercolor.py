# Generated by Django 2.2 on 2022-04-05 07:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0015_player_issupporter"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="userColor",
            field=models.CharField(default="firebrick", max_length=100),
        ),
    ]
