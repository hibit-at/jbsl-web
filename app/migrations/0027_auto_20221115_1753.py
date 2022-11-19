# Generated by Django 2.2 on 2022-11-15 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0026_playlist_ishidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='score',
            name='pos',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='score',
            name='rank',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='score',
            name='weight_acc',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='CoEditor',
            field=models.ManyToManyField(blank=True, related_name='CoEditor', to='app.Player'),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='description',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='songs',
            field=models.ManyToManyField(blank=True, to='app.Song'),
        ),
    ]