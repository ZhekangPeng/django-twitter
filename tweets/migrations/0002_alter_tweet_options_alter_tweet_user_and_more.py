# Generated by Django 4.2 on 2023-10-17 19:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tweets', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tweet',
            options={'ordering': ('user', '-created_at')},
        ),
        migrations.AlterField(
            model_name='tweet',
            name='user',
            field=models.ForeignKey(help_text='who posted the tweet', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterIndexTogether(
            name='tweet',
            index_together={('user', 'created_at')},
        ),
    ]
