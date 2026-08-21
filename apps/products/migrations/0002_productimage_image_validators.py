import apps.products.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(
                upload_to='products/%Y/%m/',
                validators=[apps.products.models.validate_image_size],
            ),
        ),
    ]
