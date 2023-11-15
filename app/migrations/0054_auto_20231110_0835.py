# Generated by Django 3.2.18 on 2023-11-09 23:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0053_alter_jpmap_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='isApplied',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='song',
            name='isUsed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='songinfo',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info', to='app.song'),
        ),
    ]