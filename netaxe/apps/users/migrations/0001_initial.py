# Generated by Django 3.2.17 on 2023-03-01 15:09

import django.contrib.auth.models
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(db_index=True, help_text='用户账号', max_length=150, unique=True, verbose_name='用户账号')),
                ('nick_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='昵称')),
                ('mobile', models.CharField(blank=True, max_length=11, null=True, verbose_name='手机号码')),
                ('email', models.EmailField(blank=True, help_text='邮箱', max_length=255, null=True, verbose_name='邮箱')),
                ('image', models.ImageField(default='images/default.png', upload_to='images/%Y/%m/%d/')),
                ('login_status', models.SmallIntegerField(choices=[(0, '在线'), (1, '离线'), (2, '忙碌')], default=0, verbose_name='登录状态')),
                ('gender', models.IntegerField(blank=True, choices=[(0, '未知'), (1, '男'), (2, '女')], default=0, help_text='性别', null=True, verbose_name='性别')),
                ('user_type', models.IntegerField(blank=True, choices=[(0, '后台用户'), (1, '前台用户')], default=0, help_text='用户类型', null=True, verbose_name='用户类型')),
                ('jwt_secret', models.UUIDField(default=uuid.uuid4)),
            ],
            options={
                'verbose_name': '用户表',
                'verbose_name_plural': '用户表',
                'db_table': 'ops_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='BgBu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='业务名称')),
            ],
            options={
                'verbose_name': '业务表',
                'verbose_name_plural': '业务表',
                'db_table': 'bgbu',
            },
        ),
        migrations.AddIndex(
            model_name='bgbu',
            index=models.Index(fields=['name'], name='bgbu_name_7454a1_idx'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
