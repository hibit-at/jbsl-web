# Generated by Django 2.2 on 2022-11-07 03:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0021_auto_20220703_2343"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="ownerComment",
            field=models.CharField(default="", max_length=1000),
        ),
    ]
