# Generated by Django 2.2 on 2023-03-07 13:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0045_auto_20230216_1509"),
    ]

    operations = [
        migrations.CreateModel(
            name="DGA",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "beatleader",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("dance", models.FloatField()),
                ("gorilla", models.FloatField()),
                ("song_mapper", models.CharField(max_length=1000)),
                ("sid", models.CharField(max_length=100)),
            ],
        ),
    ]
