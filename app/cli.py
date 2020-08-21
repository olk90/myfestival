import os
import shutil
import click
from datetime import date
from pathlib import Path

from app import db
from app.logic import create_user, create_festival, create_pku
from app.containers import UserAccessLevel
from app.models import User, PackagingUnitType
from config import Config


def __setup_owner(username):
    users = User.query.all()
    if len(users) == 0:
        create_user(username=username, access_level=UserAccessLevel.OWNER)
        print('User {} created.'.format(username)
              + ' Change password immediately after first login!')
    else:
        print('Found {} user(s) in database. Skipped creation of owner!'
              .format(len(users)))
    Path(Config.UPLOADED_PHOTOS_DEST).mkdir(parents=True, exist_ok=True)


def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language."""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system(
                'pybabel init -i messages.pot -d app/translations -l ' + lang):
            raise RuntimeError('init command failed')
        os.remove('messages.pot')

    @translate.command()
    def update():
        """Update all languages."""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i messages.pot -d app/translations'):
            raise RuntimeError('update command failed')
        os.remove('messages.pot')

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system('pybabel compile -d app/translations'):
            raise RuntimeError('compile command failed')

    @app.cli.group()
    def install():
        """Prepare default settings before (first) launch"""
        pass

    @install.command()
    @click.option('--username', default='admin')
    def admin(username):
        """Set up owner of the installation"""
        print('Prepare creation of first user')
        __setup_owner(username)

    @install.command()
    def masterdata():
        """Creates mandatory default data such as PKU"""
        print('Prepare creation of packaging unit types')
        pku = PackagingUnitType.query.all()
        if len(pku) == 0:
            create_pku()
        else:
            print('Found {} types in database. Skipped creation of PKU!'
                  .format(len(pku)))

    @install.command()
    def testdata():
        """Creates some data for manual tests"""
        print('Prepare test data creation')
        users = User.query.all()
        if len(users) == 0:
            print('Create users')
            __setup_owner(username='Batman')
            create_user(username='Wonderwoman',
                        access_level=UserAccessLevel.ADMIN)
            create_user(username='Flash')
            create_user(username='Aquaman')

            print('Create festivals')
            create_festival('Summerbreeze',
                            start=date(2019, 8, 13),
                            end=date(2019, 8, 18))
            create_festival('Bierfest',
                            start=date(2019, 3, 13),
                            end=date(2019, 3, 15))
            create_festival('Wacken',
                            start=date(2019, 8, 1),
                            end=date(2019, 8, 6))

            create_pku()
        else:
            print('Found {} user(s) in database. Skipped testdata creation'
                  .format(len(users)))

    @app.cli.group()
    def postgres():
        """Collection of helpers for managing the database"""
        pass

    @postgres.command('delete')
    def delete_tables():
        """Deletes entries from all tables without dropping them"""
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            print('Clear table {}'.format(table))
            db.session.execute(table.delete())
        db.session.commit()

    @postgres.command()
    def drop():
        """Drops current schema"""
        print('Drop all tables')
        db.session.remove()
        db.engine.execute('DROP TABLE IF EXISTS alembic_version')
        db.drop_all()

    @postgres.command()
    def initschema():
        """Drops current schema and executes flask db upgrade"""
        print('Drop all tables')
        db.session.remove()
        db.engine.execute('DROP TABLE IF EXISTS alembic_version')
        db.drop_all()
        print('Delete old profile photos')
        dir_path = Config.UPLOADED_PHOTOS_DEST
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))
        os.system('flask db upgrade')
