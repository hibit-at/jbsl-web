# Generated by Django 2.2 on 2022-02-28 15:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_auto_20220301_0023"),
    ]

    operations = [
        migrations.AlterField(
            model_name="playlist",
            name="recommend",
            field=models.ManyToManyField(
                blank=True, related_name="recommend", to="app.Song"
            ),
        ),
    ]
