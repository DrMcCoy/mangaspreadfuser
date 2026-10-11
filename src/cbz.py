# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab:

"""! CBZ files.
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

import copy
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator
from zipfile import ZipFile

from PIL import Image


class CBZ:  # pylint: disable=too-few-public-methods
    """! A CBZ file.
    """

    def __init__(self, cbz: str | Path) -> None:
        self._path = Path(cbz)
        self._cbz = ZipFile(self._path)  # pylint: disable=consider-using-with

    def __enter__(self):
        self._cbz.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._cbz.__exit__(exc_type, exc_val, exc_tb)

    def get_path(self) -> Path:
        """! Return the path of this CBZ file.
        """
        return self._path

    def get_page_names(self, sort_fn: Callable[[Any], Any] | None = str.lower) -> list[str]:
        """! Get a list of page file names in this CBZ.

        Every image file counts as a page.

        @param sort_fn  The function to use to sort the list. If None, don't sort the list.

        @return All file names of pages in this CBZ as an optionally sorted list.

        """

        page_names: list[str] = []

        for name in self._cbz.namelist():
            info = self._cbz.getinfo(name)

            if info.is_dir():
                continue

            for image_file in CBZ._get_image_extensions():
                if name.lower().endswith(image_file):
                    page_names.append(name)
                    break

        if sort_fn is not None:
            page_names.sort(key=sort_fn)

        return page_names

    def get_page_count(self) -> int:
        """! Get the number of pages in this CBZ.

        Every image file counts as a page.

        @return The number of pages in this CBZ.
        """

        return len(self.get_page_names(sort_fn=None))

    @contextmanager
    def get_page(self, page_name: str) -> Iterator[Image.Image]:
        """! Get a page within this CBZ as an Image.

        @param page_name  The name of the page as returned by get_page_names().

        @return An Image of the page within a Context.
        """

        file_info = self._cbz.getinfo(page_name)

        with self._cbz.open(file_info) as page_file:
            with Image.open(page_file) as image:
                yield image

    def rewrite(self, cbz: str | Path,
                files_to_add: list[tuple[str | Path, bytes]] | None = None,
                files_to_delete: list[str | Path] | None = None,
                files_to_rename: dict[str, str] | None = None,
                overwrite: bool = False) -> None:
        """! Copy this CBZ contents into a new CBZ, optionally removing, adding and renaming files.

        @param cbz              The filename of the new CBZ.
        @param files_to_add     A list of files to add, path and contents.
        @param files_to_delete  A list of file paths to delete.
        @param files_to_rename  A list of file paths to rename, a dict to map old -> new.
        """

        if files_to_delete is None:
            files_to_delete = []
        if files_to_add is None:
            files_to_add = []
        if files_to_rename is None:
            files_to_rename = {}

        to_delete = []
        to_delete.extend([str(file).lower() for file in files_to_delete])
        to_delete.extend([files_to_rename.get(str(file[0]).lower(), str(file[0]).lower()) for file in files_to_add])

        count = len(self._cbz.infolist()) + len(files_to_add)

        with ZipFile(cbz, "w" if overwrite else "x") as new_cbz:
            new_cbz.comment = self._cbz.comment

            index = 0

            for old_item in self._cbz.infolist():
                if str(old_item.filename).lower() in to_delete:
                    print(f"{index}/{count - 1}: - {old_item.filename}")
                    index = index + 1
                    continue

                new_item = copy.copy(old_item)
                new_item.filename = files_to_rename.get(str(new_item.filename).lower(), str(new_item.filename))

                buffer = self._cbz.read(old_item)
                new_cbz.writestr(new_item, buffer)

                if old_item.filename != new_item.filename:
                    print(f"{index}/{count - 1}: > {old_item.filename} -> {new_item.filename}")
                else:
                    print(f"{index}/{count - 1}: = {new_item.filename}")

                index = index + 1

            for add_file in files_to_add:
                new_name = files_to_rename.get(str(add_file[0]), str(add_file[0]))
                new_cbz.writestr(new_name, add_file[1])

                print(f"{index}/{count - 1}: + {new_name}")
                index = index + 1

    @staticmethod
    def _get_image_extensions() -> set[str]:
        Image.init()

        return set(Image.registered_extensions().keys())
