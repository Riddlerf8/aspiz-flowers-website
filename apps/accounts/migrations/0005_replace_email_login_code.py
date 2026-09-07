import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_emaillogincode"),
    ]

    login_code_fields = [
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("code_hash", models.CharField(max_length=128)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("expires_at", models.DateTimeField()),
        ("attempts", models.PositiveSmallIntegerField(default=0)),
        ("used_at", models.DateTimeField(blank=True, null=True)),
        (
            "user",
            models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_codes",
                to="accounts.user",
            ),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS `accounts_logincode` ("
                        "`id` bigint NOT NULL AUTO_INCREMENT, "
                        "`code_hash` varchar(128) NOT NULL, "
                        "`created_at` datetime(6) NOT NULL, "
                        "`expires_at` datetime(6) NOT NULL, "
                        "`attempts` smallint unsigned NOT NULL, "
                        "`used_at` datetime(6) NULL, "
                        "`user_id` bigint NOT NULL, "
                        "PRIMARY KEY (`id`), "
                        "CONSTRAINT `accounts_logincode_user_id_fk_accounts_user_id` "
                        "FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)"
                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name="EmailLoginCode"),
                migrations.CreateModel(
                    name="LoginCode",
                    fields=login_code_fields,
                    options={"ordering": ["-created_at"]},
                ),
                migrations.AlterModelOptions(name="user", options={}),
            ],
        ),
    ]
