import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from db import TAGS, NOTES, NOTE_TAGS, create_tables
from sqlalchemy import create_engine, exists, literal
from sqlalchemy.sql import select
from sqlalchemy_utils.functions import database_exists


DEFAULT_EDITOR = '/usr/bin/vi'
DEFAULT_CONFIG = Path.home() / '.xnote.config.yml'

logging.basicConfig()
LOG = logging.getLogger(__name__)


def _filter_by_tag(query, tag):
    return query.where(TAGS.c.tag == tag).select_from(
        NOTE_TAGS.join(
            TAGS, TAGS.c.id == NOTE_TAGS.c.tag_id
        ).join(
            NOTES, NOTES.c.id == NOTE_TAGS.c.note_id
        )
    )


def _connect_to_database(database_uri, sql_echo):
    if database_exists(database_uri):
        engine = create_engine(database_uri, echo=sql_echo)
        db_conn = engine.connect()
    else:
        LOG.fatal(f"Database {database_uri} does not exist!")
        db_conn = None

    return db_conn


class App:
    def __init__(self):
        self._config = None
        self._conn = None

    @property
    def editor(self):
        return self._config.get('editor', DEFAULT_EDITOR)

    def config(self, config_path=None):
        config_path = config_path or DEFAULT_CONFIG
        if config_path is not None and config_path.exists():
            self._config = yaml.safe_load(config_path.read_text())
            database_uri = self._config['database']
            sql_echo = self._config.get('sql_echo', True)
            self._conn = _connect_to_database(database_uri, sql_echo)
        else:
            LOG.fatal("Quit: NO config file found! Default: %s.", DEFAULT_CONFIG)
            sys.exit(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._conn:
            self._conn.close()

    def init_db(self, args):
        database_uri = self._config['database']
        sql_echo = self._config.get('sql_echo', True)
        if not database_exists(database_uri):
            LOG.info("Initialize the database: %s", database_uri)
            engine = create_engine(database_uri, echo=sql_echo)
            create_tables(engine)
        else:
            LOG.warning(f"Database {database_uri} already exists!")

    def list_notes(self, args):
        """
        List view of the notes.

        :param args:
        :return:
        """
        query = select([NOTES])
        if args.first is not None:
            query = query.where(NOTES.c.id >= args.first)
        if args.last is not None:
            query = query.where(NOTES.c.id <= args.last)
        if args.tag is not None:
            query = _filter_by_tag(query, args.tag)

        for row in self._execute(query):
            print("{id:4d}: [{time}] {title:s}".format(**row))

    def show_note(self, args, *, note_id=None):
        """
        Show one note.

        :param note_id:
        :param args:
        :return:
        """
        note_id = note_id or args.note_id
        query = select([NOTES]).where(NOTES.c.id == note_id)
        tags_ = self._get_tags(note_id)
        row = self._execute(query).first()
        if row:
            sep = "# " + "-" * 25
            print("#{:5d}: {} {:s}".format(
                *[row[k] for k in ('id', 'time', 'title')]))
            print(sep)
            if tags_:
                print(f"# TAGS: {','.join(tags_)}")
                print(sep)
            print(f"{row['body']}")

    def remove_note(self, args, *, note_id=None):
        note_id = note_id or args.note_id
        statement = NOTES.delete().where(NOTES.c.id == note_id)
        self._execute(statement)

    def add_note(self, args, *, title=None, body=None, tags_=None):
        tags_ = tags_ or args.tags
        title = title or args.title
        content = body
        if content is None and args.file:
            content = Path(args.file).read_text()

        if content is None:
            content = self._edit_note()
            title = content.split('\n', 1)[0].strip()

        if title:
            statement = NOTES.insert().values(title=title, body=content)
            result = self._execute(statement)
            note_id = result.lastrowid
            LOG.info(f'note %s added', note_id)
            if tags_:
                for tag in tags_.split(','):
                    self.add_tag(args, tag_=tag)
                    self.annotate_note(args, note_id=note_id, tag_=tag)
            return note_id

    def annotate_note(self, args, *, note_id=None, tag_=None):
        tag_ = tag_ or args.tag
        note_id = note_id or args.note_id
        query = select(
            [literal(note_id).label('note_id'), TAGS.c.id.label('tag_id')]
        ).where(TAGS.c.tag == tag_)
        statement = NOTE_TAGS.insert().from_select(
            ['note_id', 'tag_id'], query)
        self._conn.execute(statement)

    def find_notes(self, args):
        columns = [NOTES.c.id, NOTES.c.time, NOTES.c.title]
        query = select(columns)
        if args.tag is not None:
            query = _filter_by_tag(query, args.tag)
        if args.word is not None:
            query = query.where(NOTES.c.body.like(f'%{args.word}%'))

        rows = self._execute(query).fetchall()
        if len(rows) == 1:
            self.show_note(None, note_id=rows[0]['id'])
        else:
            for row in rows:
                print("{id:4d}: [{time}] {title:s}".format(**row))

    def update_note(self, args, *, title=None, content=None, note_id=None):
        note_id = note_id or args.note_id
        query = select([NOTES.c.body]).where(NOTES.c.id == note_id)

        new_title = title
        new_content = content

        if new_title is None or new_content is None:
            old_content = self._execute(query).fetchone()['body']
            new_content = self._edit_note(old_content)
            new_title = new_content.split('\n', 1)[0].strip()

        statement = NOTES.update().where(NOTES.c.id == note_id).values(
            title=new_title,
            body=new_content
        )
        self._execute(statement)

    def list_tags(self, args):
        query = select([TAGS])
        for row in self._conn.execute(query):
            print("{:4d}: {:s}".format(*row))

    def add_tag(self, args, *, tag_=None):
        tag_ = tag_ or args.tag
        query = select([literal(tag_).label('tag')]).where(
            ~exists([TAGS.c.tag]).where(TAGS.c.tag == tag_)
        )
        statement = TAGS.insert().from_select(['tag'], query)
        out = self._execute(statement)
        return out.lastrowid

    def remove_tag(self, args, *, tag_=None):
        tag_ = tag_ or args.tag
        statement = TAGS.delete().where(TAGS.c.tag == tag_)
        self._execute(statement)

    def update_tag(self, args, *, old_tag=None, new_tag=None):
        old_tag = old_tag or args.old_tag
        new_tag = new_tag or args.new_tag
        statement = TAGS.update().where(
            TAGS.c.tag == old_tag
        ).where(
            ~exists([TAGS.c.tag]).where(TAGS.c.tag == new_tag)
        ).values(tag=new_tag)
        self._execute(statement)

    def _get_tags(self, note_id):
        query = select([TAGS.c.tag]).where(
            NOTE_TAGS.c.note_id == note_id
        ).select_from(NOTE_TAGS.join(TAGS, TAGS.c.id == NOTE_TAGS.c.tag_id))
        out = self._conn.execute(query)
        return [row['tag'] for row in out]

    def _edit_note(self, content=None):
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            f.write(content or '')
            f.flush()
            subprocess.check_call([self.editor, f.name])
            f.seek(0, 0)
            text = f.read()

        return text.strip()

    def _execute(self, statement):
        if self._conn is not None:
            return self._conn.execute(statement)
        else:
            LOG.fatal("Quit: Connection to database: %s failed!",
                      self._config['database'])
            sys.exit(1)
