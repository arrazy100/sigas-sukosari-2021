# Generated by Django 3.2.4 on 2021-06-19 00:06

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0003_materi'),
    ]

    operations = [
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='materi',
            name='form_hash',
            field=models.CharField(default=datetime.datetime(2021, 6, 19, 0, 6, 21, 405057, tzinfo=utc), max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='materi',
            name='token',
            field=models.CharField(default=123456, max_length=6),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='FileSiswa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=200)),
                ('keterangan', models.TextField()),
                ('uploaded_at', models.DateField(default=datetime.datetime(2021, 6, 19, 0, 5, 39, 376837))),
                ('materi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='task_management.materi')),
            ],
        ),
    ]