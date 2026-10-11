# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab:

"""! Main entry point for MangaSpreadFuser.
"""

# MangaSpreadFuser - Fuse split manga spread pages in CBZ
#
# MangaSpreadFuser is the legal property of its developers,
# whose names can be found in the AUTHORS file distributed with this source
# distribution.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import sys
from typing import Any

from mangaspreadfuser import MangaSpreadFuser
from util import Util


class Main:  # pylint: disable=too-few-public-methods
    """! Frame that runs the main application.
    """

    @staticmethod
    def _print_version() -> None:
        """! Print version information.
        """

        info: dict[str, Any] = Util.get_project_info()

        # Print program version information
        print(f"{info['name']} {info['version']}")
        print()
        print(f"Copyright (c) {info['years']} {', '.join(info['authors'])}")
        print()
        print("This is free software; see the source for copying conditions.  There is NO")
        print("warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.")

    @staticmethod
    def _parse_args() -> argparse.Namespace:
        """! Parse command line arguments.

        @return An object containing the parsed command line arguments.
        """
        info: dict[str, Any] = Util.get_project_info()
        nameversion: str = f"{info['name']} {info['version']}"
        description: str = f"{nameversion} -- {info['summary']}"

        parser: argparse.ArgumentParser = argparse.ArgumentParser(description=description, add_help=False)

        # Note: we're setting required to False even on required arguments and do the checks
        # ourselves below. We're doing that because we want more dynamic --version behaviour

        parser.add_argument('-h', '--help', action="help", help='Show this help message and exit')
        parser.add_argument("-v", "--version", required=False, action="store_true",
                            help="Print the version and exit")

        parser.add_argument("-s", "--start_index", required=False, type=int, default=0,
                            help="Page index to start looking for spreads (default: 0)")

        parser.add_argument("-r", "--right-to-left", required=False, action="store_true",
                            help="It's a manga with right-to-left read order (default: True)")
        parser.add_argument("-l", "--left-to-right", required=False, action="store_true",
                            help="It's a comic with left-to-right read order (default: False)")

        parser.add_argument("-f", "--overwrite", required=False, action="store_true",
                            help="Overwrite existing CBZ files (default: False)")

        parser.add_argument("-m", "--mode", required=False,
                            choices=["add_before", "add_middle", "add_after", "replace"], default="add_before",
                            help="What to do with fused pages (default: add_before)")

        parser.add_argument("-n", "--renumber", required=False, action="store_true",
                            help="Renumber the page image files in the CBZ (default: False)")
        parser.add_argument("-w", "--min-width", required=False, type=int, default=4,
                            help="Minimum number of digits for a page image filename (default: 4, ie. 0001.jpg)")

        parser.add_argument("files", nargs='*', metavar="<cbz to process>",
                            help="A CBZ file to process")

        args: argparse.Namespace = parser.parse_args()

        if args.version:
            Main._print_version()
            parser.exit()

        if args.files is None or len(args.files) < 1:
            parser.print_help()
            parser.exit()

        if args.right_to_left and args.left_to_right:
            parser.error("both right-to-left and -left-to-right have been specified: "
                         "-r/--right-to-left, -l/--left-to-right")

        return args

    def run(self) -> int:
        """! Run the main MangaSpreadFuser application.
        """
        args: argparse.Namespace = Main._parse_args()

        mangaspreadfuser: MangaSpreadFuser = MangaSpreadFuser(args)
        return mangaspreadfuser.run()


def main() -> int:
    """! MangaSpreadFuser main function, running the main app.
    """
    main_app: Main = Main()
    return main_app.run()


if __name__ == '__main__':
    sys.exit(main())
