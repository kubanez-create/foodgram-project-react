# Generated by Django 3.2.16 on 2023-03-28 05:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20230327_0620'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipes',
            old_name='is_favored',
            new_name='favored',
        ),
        migrations.RenameField(
            model_name='recipes',
            old_name='is_in_shopping_cart',
            new_name='in_shopping_cart',
        ),
    ]