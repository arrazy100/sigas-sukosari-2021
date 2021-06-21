# Generated by Django 3.2.4 on 2021-06-19 00:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0004_auto_20210619_0006'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Files',
        ),
        migrations.AddField(
            model_name='filesiswa',
            name='filename',
            field=models.CharField(default='tes.pdf', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='filesiswa',
            name='uploaded_at',
            field=models.DateField(default=datetime.datetime(2021, 6, 19, 0, 8, 6, 732243)),
        ),
    ]