# Generated by Django 3.2.16 on 2023-01-02 06:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0004_alter_metadatafield_unique_together'),
    ]

    operations = [
        migrations.RenameField(
            model_name='metadata',
            old_name='field_data',
            new_name='field_value',
        ),
    ]
