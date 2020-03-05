from sqlalchemy import (
    MetaData,
    UniqueConstraint, ForeignKey,
    Table, Column, Integer, String, DateTime,
    func
)

__all__ = ['TAGS', 'NOTES', 'NOTE_TAGS', 'create_tables']

meta = MetaData()

TAGS = Table(
    'tags', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tag', String, nullable=False),
    UniqueConstraint('tag')
)

NOTES = Table(
    'notes', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('time', Integer, ForeignKey('users.id'), nullable=False),
    Column('time', DateTime, nullable=False, default=func.now()),
    Column('title', String, nullable=False),
    Column('body', String, nullable=False)
)

NOTE_TAGS = Table(
    'note_tags', meta,
    Column('note_id', Integer, ForeignKey('notes.id'), nullable=False),
    Column('tag_id', Integer, ForeignKey('tags.id'), nullable=False),
)


def create_tables(engine):
    meta.create_all(engine)
