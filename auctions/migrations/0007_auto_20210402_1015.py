# Generated by Django 3.1.7 on 2021-04-02 08:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_watchlist'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name']},
        ),
    ]