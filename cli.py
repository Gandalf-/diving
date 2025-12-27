#!/usr/bin/python3
"""Unified CLI for diving utilities."""

import argparse

from diving import imprecise, missing


def main() -> None:
    parser = argparse.ArgumentParser(description='Diving utilities')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # imprecise subcommand
    imp = subparsers.add_parser('imprecise', help='Find and update imprecise image names')
    imp.add_argument('-l', '--list', action='store_true', help='list imprecise names')
    imp.add_argument('-f', '--find', metavar='NAME', help='find imprecise images by name')
    imp.add_argument('-u', '--update', metavar='NAME', help='update imprecise images by name')

    # missing subcommand
    mis = subparsers.add_parser('missing', help='Find missing or incomplete taxonomy data')
    mis.add_argument(
        '-m', '--missing', action='store_true', help='list names without taxonomy entry'
    )
    mis.add_argument(
        '-i', '--incomplete', action='store_true', help='list names without exact genus+species'
    )

    args = parser.parse_args()

    if args.command == 'imprecise':
        if args.list:
            imprecise.main_list()
        elif args.find:
            imprecise.save_imprecise(args.find)
        elif args.update:
            imprecise.update_imprecise(args.update)
        else:
            imp.print_help()

    elif args.command == 'missing':
        if args.missing:
            missing.main_missing()
        elif args.incomplete:
            missing.main_incomplete()
        else:
            mis.print_help()


if __name__ == '__main__':
    main()
