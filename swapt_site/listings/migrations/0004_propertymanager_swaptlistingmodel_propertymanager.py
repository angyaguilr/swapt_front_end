# Generated by Django 4.1.4 on 2023-03-18 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_listing_categoryv2'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyManager',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('propertyname', models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='swaptlistingmodel',
            name='propertymanager',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='listings.propertymanager'),
        ),
    ]
