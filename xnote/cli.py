import argparse
from pathlib import Path

__all__ = ['get_parser']

from app import App


def get_parser(app: App):
    parser = argparse.ArgumentParser(prog='xnote')
    parser.add_argument(
        '-c', '--config_path', type=lambda p: Path(p),
        help='config file path'
    )
    subparsers = parser.add_subparsers(help='sub-commands', dest='cmd')
    add_database_subparser(app, subparsers)
    add_tags_subparser(app, subparsers)
    add_note_subparser(app, subparsers)
    return parser


def add_database_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('initdb', help='initialized database')
    parser.set_defaults(func=app.init_db)


def add_tags_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('tags', help='manage tags')

    subparsers = parser.add_subparsers(
        help='sub-commands for tags', dest='tag_cmd')

    list_parser = subparsers.add_parser('ls', help='list tags')
    list_parser.set_defaults(func=app.list_tags)

    add_parser = subparsers.add_parser('add', help='add a tag')
    add_parser.add_argument('tag', help='create a new tag')
    add_parser.set_defaults(func=app.add_tag)

    rm_parser = subparsers.add_parser('rm', help='del a tag')
    rm_parser.add_argument('tag', help='delete a new tag')
    rm_parser.set_defaults(func=app.remove_tag)

    up_parser = subparsers.add_parser('up', help='update a tag')
    up_parser.add_argument('old_tag', help='old tag')
    up_parser.add_argument('new_tag', help='new tag')
    up_parser.set_defaults(func=app.update_tag)


def add_note_subparser(app: App, app_subparsers):
    add_list_subparser(app, app_subparsers)
    add_show_subparser(app, app_subparsers)
    add_find_subparser(app, app_subparsers)
    add_edit_subparser(app, app_subparsers)
    add_ann_subparser(app, app_subparsers)
    add_add_subparser(app, app_subparsers)
    add_remove_subparser(app, app_subparsers)


def add_list_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('ls', help='list all notes')
    parser.add_argument('-t', '--tag',
                        help='only list notes with the specified tag')
    parser.add_argument('-f', '--first', type=int,
                        help='first id to list')
    parser.add_argument('-l', '--last', type=int,
                        help='last id to list')
    parser.set_defaults(func=app.list_notes)


def add_show_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser(
        'show', help='show the note with the specified id')
    parser.add_argument('note_id', type=int, help='note id')
    parser.set_defaults(func=app.show_note)


def add_edit_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('edit', help='edit a note')
    parser.add_argument('note_id', type=int, help='note id')
    parser.set_defaults(func=app.update_note)


def add_ann_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser(
        'ann', help='annotate a note by adding a tag')
    parser.add_argument('note_id', type=int, help='note id')
    parser.add_argument('tag', help='tag')
    parser.set_defaults(func=app.annotate_note)


def add_find_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('find', help='find notes')
    parser.add_argument('word', nargs='?', help='the keyword to find')
    parser.add_argument(
        '-t', '--tag', help='find only the notes with the specified tag')
    parser.set_defaults(func=app.find_notes)


def add_add_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('add', help='add a note')
    parser.add_argument('-f', '--file', help='add a file as a note')
    parser.add_argument('-T', '--title', help='title for the note')
    parser.add_argument('-t', '--tags', help='tags for the note')
    parser.set_defaults(func=app.add_note)


def add_remove_subparser(app: App, app_subparsers):
    parser = app_subparsers.add_parser('rm', help='remove a note by note_id')
    parser.add_argument('note_id', type=int, help='note id')
    parser.set_defaults(func=app.remove_note)
