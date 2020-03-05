from cli import get_parser
from app import App


def main():
    with App() as app:
        parser = get_parser(app)
        args = parser.parse_args()
        app.config(args.config_path)
        if 'func' in args:
            args.func(args)
        else:
            parser.print_help()


if __name__ == '__main__':
    main()
