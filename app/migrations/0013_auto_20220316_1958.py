# Generated by Django 2.2 on 2022-03-16 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20220316_1933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='headline',
            name='player',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Player'),
        ),
    ]
