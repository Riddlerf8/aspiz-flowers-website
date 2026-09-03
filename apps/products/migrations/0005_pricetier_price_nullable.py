from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_remove_translation_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pricetier",
            name="price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Boş bırakılırsa bu kademe 'DM' (mesajla fiyat) olarak gösterilir — "
                    "örn. 400 adet ve üzeri için sabit fiyat yerine WhatsApp'tan fiyat alınır. "
                    "Sadece en yüksek adetli kademe boş bırakılabilir."
                ),
                max_digits=10,
                null=True,
            ),
        ),
    ]
