# Generated by Django 5.1.7 on 2025-03-09 09:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackingData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acc_x', models.FloatField(blank=True, help_text='Nilai akselerasi sumbu X', null=True)),
                ('acc_y', models.FloatField(blank=True, help_text='Nilai akselerasi sumbu Y', null=True)),
                ('acc_z', models.FloatField(blank=True, help_text='Nilai akselerasi sumbu Z', null=True)),
                ('latitude', models.FloatField(blank=True, help_text='Latitude dari GPS', null=True)),
                ('longitude', models.FloatField(blank=True, help_text='Longitude dari GPS', null=True)),
                ('speed', models.FloatField(blank=True, help_text='Kecepatan (km/jam)', null=True)),
                ('accident', models.BooleanField(default=False, help_text='Status kecelakaan')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='Waktu data diterima')),
                ('user', models.ForeignKey(blank=True, help_text='User yang terkait dengan data pelacakan (jika ada)', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
