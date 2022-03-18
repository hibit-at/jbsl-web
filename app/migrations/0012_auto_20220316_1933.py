# Generated by Django 2.2 on 2022-03-16 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20220313_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='isLive',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='score',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='app.Song'),
        ),
    ]