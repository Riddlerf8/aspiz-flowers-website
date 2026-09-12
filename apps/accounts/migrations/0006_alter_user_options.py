from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_replace_email_login_code"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "user", "verbose_name_plural": "users"},
        ),
    ]
