# Generated by Django 2.2 on 2023-01-24 07:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0039_auto_20230124_1623"),
    ]

    operations = [
        migrations.AddField(
            model_name="jpmap",
            name="uploader",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="app.Player",
            ),
        ),
    ]
