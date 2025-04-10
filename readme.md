# Dans mysql

CREATE DATABASE votre_bdd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Activer votre environnement virtuel

.\venv\Script\activate

# Installer python-decouple

pip install python-decouple

# Configurer le .env comme ceci

SECRET_KEY=django-insecure-ok=)y#ey-@bm0x&k-4b^d)05p%$v@fx7t!tp#cmev4rb-t)1pj
DEBUG=True
DB_NAME=votre_bdd
DB_USER=user_mysql
DB_PASSWORD=mot_de_passe_mysql
DB_HOST=Votre_host (localhost ou autre)
DB_PORT=votre_port

# Faire les migrations

python manage.py makemigration
python manage.py migrate

# Lancer le projet

python manage.py runserver