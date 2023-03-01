# Generated by Django 3.2.17 on 2023-03-01 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Topology',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='名称')),
                ('memo', models.TextField(blank=True, null=True, verbose_name='描述')),
            ],
            options={
                'verbose_name_plural': '拓扑表',
                'db_table': 'topology',
            },
        ),
        migrations.AddIndex(
            model_name='topology',
            index=models.Index(fields=['name'], name='topology_name_89fd82_idx'),
        ),
    ]
