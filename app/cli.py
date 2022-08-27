import os
import shutil
from datetime import date
from pathlib import Path

import click
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.schema import DropConstraint, DropTable, MetaData, Table

from app import db, session
from app.containers import UserAccessLevel
from app.logic import create_user, create_festival, create_pku
from app.models import User, PackagingUnitType
from config import Config


def __setup_owner(username):
    users = session.query(User).all()
    if len(users) == 0:
        create_user(username=username, access_level=UserAccessLevel.OWNER)
        print("User {} created.".format(username)
              + " Change password immediately after first login!")
    else:
        print("Found {} user(s) in database. Skipped creation of owner!"
              .format(len(users)))
    Path(Config.UPLOADED_PHOTOS_DEST).mkdir(parents=True, exist_ok=True)


def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    @click.argument("lang")
    def init(lang):
        """Initialize a new language."""
        if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
            raise RuntimeError("extract command failed")
        if os.system(
                "pybabel init -i messages.pot -d app/translations -l " + lang):
            raise RuntimeError("init command failed")
        os.remove("messages.pot")

    @translate.command()
    def update():
        """Update all languages."""
        if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
            raise RuntimeError("extract command failed")
        if os.system("pybabel update -i messages.pot -d app/translations"):
            raise RuntimeError("update command failed")
        os.remove("messages.pot")

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system("pybabel compile -d app/translations"):
            raise RuntimeError("compile command failed")

    @app.cli.group()
    def install():
        """Prepare default settings before (first) launch"""
        pass

    @install.command()
    @click.option("--username", default="admin")
    def admin(username):
        """Set up owner of the installation"""
        print("Prepare creation of first user")
        __setup_owner(username)

    @install.command()
    def masterdata():
        """Creates mandatory default data such as PKU"""
        print("Prepare creation of packaging unit types")

        pku = session.query(PackagingUnitType).all()
        if len(pku) == 0:
            create_pku()
        else:
            print("Found {} types in database. Skipped creation of PKU!"
                  .format(len(pku)))

    @install.command()
    def testdata():
        """Creates some data for manual tests"""
        print("Prepare test data creation in database {}".format(Config.SQLALCHEMY_DATABASE_URI))
        users = session.query(User).all()
        if len(users) == 0:
            print("Create users")
            __setup_owner(username="Batman")
            create_user(username="Wonderwoman",
                        access_level=UserAccessLevel.ADMIN)
            create_user(username="Flash")
            create_user(username="Aquaman")

            print("Create festivals")
            create_festival("Summerbreeze",
                            start=date(2019, 8, 13),
                            end=date(2019, 8, 18))
            create_festival("Bierfest",
                            start=date(2019, 3, 13),
                            end=date(2019, 3, 15))
            create_festival("Wacken",
                            start=date(2019, 8, 1),
                            end=date(2019, 8, 6))

            create_pku()
        else:
            print("Found {} user(s) in database. Skipped testdata creation"
                  .format(len(users)))

    @app.cli.group()
    def postgres():
        """Collection of helpers for managing the database"""
        pass

    @postgres.command("delete")
    def delete_tables():
        """Deletes entries from all tables without dropping them"""
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            print("Clear table {}".format(table))
            session.execute(table.delete())
        session.commit()

    @postgres.command()
    def drop():
        """Drops current schema"""
        print("Drop all tables of {}".format(Config.SQLALCHEMY_DATABASE_URI))
        session.remove()
        db.engine.execute("DROP TABLE IF EXISTS alembic_version")
        db.drop_all()

    @postgres.command()
    def initschema():
        """Drops current schema and executes flask db upgrade"""
        print("Initialize database schema for {}".format(Config.SQLALCHEMY_DATABASE_URI))
        print("Drop all tables")
        session.remove()
        db.engine.execute("DROP TABLE IF EXISTS alembic_version")
        drop_all()

        print("Delete old profile photos")
        avatars = Config.UPLOADED_PHOTOS_DEST
        try:
            shutil.rmtree(avatars)
        except OSError as e:
            print("Error: %s : %s" % (avatars, e.strerror))
        print("Delete chronicle photos")
        photos = Config.UPLOAD_PATH
        try:
            shutil.rmtree(photos)
        except OSError as e:
            print("Error: %s : %s" % (photos, e.strerror))
        os.system("flask db upgrade")

    # workaround found in https://github.com/pallets-eco/flask-sqlalchemy/issues/722#issuecomment-705672929
    def drop_all():
        """(On a live db) drops all foreign key constraints before dropping all tables.
        Workaround for SQLAlchemy not doing DROP ## CASCADE for drop_all()
        (https://github.com/pallets/flask-sqlalchemy/issues/722)
        """

        con = db.engine.connect()
        trans = con.begin()
        inspector = Inspector.from_engine(db.engine)

        # We need to re-create a minimal metadata with only the required things to
        # successfully emit drop constraints and tables commands for postgres (based
        # on the actual schema of the running instance)
        meta = MetaData()
        tables = []
        all_fkeys = []

        for table_name in inspector.get_table_names():
            fkeys = []

            for fkey in inspector.get_foreign_keys(table_name):
                if not fkey["name"]:
                    continue

                fkeys.append(db.ForeignKeyConstraint((), (), name=fkey["name"]))

            tables.append(Table(table_name, meta, *fkeys))
            all_fkeys.extend(fkeys)

        for fkey in all_fkeys:
            con.execute(DropConstraint(fkey))

        for table in tables:
            con.execute(DropTable(table))

        trans.commit()
