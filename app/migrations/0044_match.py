# Generated by Django 2.2 on 2023-02-16 02:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0043_auto_20230206_2052'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('retry1', models.BooleanField()),
                ('result1', models.IntegerField(default=0)),
                ('retry2', models.BooleanField()),
                ('result2', models.IntegerField(default=0)),
                ('map_info', models.CharField(max_length=1000)),
                ('highest_acc', models.FloatField(default=0)),
                ('state', models.IntegerField(default=0)),
                ('editor', models.ManyToManyField(to='app.Player')),
                ('now_playing', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Song')),
                ('player1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player1', to='app.Player')),
                ('player2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player2', to='app.Player')),
            ],
        ),
    ]