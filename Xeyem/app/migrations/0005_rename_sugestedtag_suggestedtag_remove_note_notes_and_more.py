# Generated by Django 4.1.1 on 2022-10-22 16:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_address_rename_address_name_entity_wallet_name_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SugestedTag',
            new_name='SuggestedTag',
        ),
        migrations.RemoveField(
            model_name='note',
            name='notes',
        ),
        migrations.AddField(
            model_name='note',
            name='date_posted',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='note',
            name='note',
            field=models.TextField(default='', max_length=5000),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='address',
            name='first_transaction',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='informant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='address',
            name='transactions',
            field=models.CharField(blank=True, max_length=1073741824, null=True),
        ),
        migrations.AlterField(
            model_name='note',
            name='wallet_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.address', to_field='address'),
        ),
        migrations.AlterField(
            model_name='webappearance',
            name='informant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
