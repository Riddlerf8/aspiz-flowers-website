from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_category_name_en_category_name_tr_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='name_en',
        ),
        migrations.RemoveField(
            model_name='category',
            name='name_tr',
        ),
        migrations.RemoveField(
            model_name='category',
            name='name_zh_hans',
        ),
        migrations.RemoveField(
            model_name='product',
            name='description_en',
        ),
        migrations.RemoveField(
            model_name='product',
            name='description_tr',
        ),
        migrations.RemoveField(
            model_name='product',
            name='description_zh_hans',
        ),
        migrations.RemoveField(
            model_name='product',
            name='name_en',
        ),
        migrations.RemoveField(
            model_name='product',
            name='name_tr',
        ),
        migrations.RemoveField(
            model_name='product',
            name='name_zh_hans',
        ),
    ]
