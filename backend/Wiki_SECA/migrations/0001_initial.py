# Generated by Django 3.2 on 2021-06-20 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('SECAAlgo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Problem_wiki',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('intro', models.CharField(max_length=1000)),
                ('image', models.CharField(max_length=100, null=True)),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SECAAlgo.predictions')),
            ],
        ),
        migrations.CreateModel(
            name='Content_wiki',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=10000)),
                ('concepts', models.CharField(max_length=1000)),
                ('image', models.CharField(max_length=100)),
                ('problem_wiki', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Wiki_SECA.problem_wiki')),
            ],
        ),
    ]
