# Generated by Django 3.2 on 2021-07-26 16:35

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('SECAAlgo', '0004_alter_annotations_bounding_box_coordinates'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExplanationSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_explanation', models.CharField(max_length=200)),
                ('image_setting', models.CharField(blank=True, max_length=200, null=True)),
                ('task_setting', models.CharField(blank=True, max_length=200, null=True)),
                ('classA', models.CharField(blank=True, max_length=200, null=True)),
                ('classB', models.CharField(blank=True, max_length=200, null=True)),
                ('explanation_list', jsonfield.fields.JSONField()),
            ],
        ),
        migrations.AddField(
            model_name='sessions',
            name='explanations',
            field=models.ManyToManyField(to='SECAAlgo.ExplanationSet'),
        ),
    ]
