# Generated by Django 3.2.17 on 2023-02-28 09:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topology', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topology',
            name='bgbu',
        ),
    ]