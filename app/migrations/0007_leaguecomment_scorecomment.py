# Generated by Django 2.2 on 2022-03-06 18:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20220304_1744'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoreComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(blank=True, default='', max_length=50)),
                ('score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Score')),
            ],
        ),
        migrations.CreateModel(
            name='LeagueComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(blank=True, default='', max_length=50)),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.League')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Player')),
            ],
        ),
    ]
