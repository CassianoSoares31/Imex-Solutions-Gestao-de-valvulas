# Shim do PyMySQL pro backend django.db.backends.mysql (que espera o pacote
# MySQLdb). Só ativa quando pymysql está instalado (requirements de produção
# c/ DB_ENGINE=mysql) — em dev local com Postgres, pymysql nem está no venv
# e isso vira no-op.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# .
