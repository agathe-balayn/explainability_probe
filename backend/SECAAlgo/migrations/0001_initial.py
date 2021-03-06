# Generated by Django 3.2 on 2021-06-20 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('UserSECA', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Images',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_name', models.CharField(max_length=50)),
                ('actual_image', models.CharField(max_length=100)),
                ('predicted_image', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Rules',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('antecedents', models.CharField(max_length=200)),
                ('consequents', models.CharField(blank=True, max_length=200)),
                ('antecedent_support', models.FloatField(blank=True, null=True)),
                ('antecedent_len', models.IntegerField(blank=True, null=True)),
                ('p_value', models.FloatField(blank=True, null=True)),
                ('cramers_value', models.FloatField(blank=True, null=True)),
                ('class_frequencies', models.TextField(blank=True)),
                ('consequent_support', models.FloatField(blank=True, null=True)),
                ('rule_support', models.FloatField(blank=True, null=True)),
                ('rule_confidence', models.FloatField(blank=True, null=True)),
                ('lift', models.FloatField(blank=True, null=True)),
                ('leverage', models.FloatField(blank=True, null=True)),
                ('conviction', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Predictions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100, unique=True)),
                ('images', models.ManyToManyField(to='SECAAlgo.Images')),
                ('users', models.ManyToManyField(to='UserSECA.SECAUser')),
            ],
        ),
        migrations.CreateModel(
            name='Notes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, null=True)),
                ('problem', models.ManyToManyField(to='SECAAlgo.Predictions')),
                ('user', models.ManyToManyField(to='UserSECA.SECAUser')),
            ],
        ),
        migrations.CreateModel(
            name='Annotations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annotation', models.CharField(max_length=50)),
                ('bounding_box_coordinates', models.CharField(max_length=50)),
                ('weight', models.IntegerField()),
                ('reason', models.CharField(blank=True, max_length=300, null=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SECAAlgo.images')),
            ],
        ),
    ]
