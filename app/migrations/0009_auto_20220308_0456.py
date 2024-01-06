# Generated by Django 2.2 on 2022-03-07 19:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0008_auto_20220307_0356"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="first",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="first",
                to="app.Player",
            ),
        ),
        migrations.AddField(
            model_name="league",
            name="second",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="second",
                to="app.Player",
            ),
        ),
        migrations.AddField(
            model_name="league",
            name="third",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="third",
                to="app.Player",
            ),
        ),
    ]
