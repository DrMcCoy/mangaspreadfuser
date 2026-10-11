# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab:

"""! The actual MangaSpreadFuser logic.
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
import io
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from PySide6.QtWidgets import QApplication

from cbz import CBZ
from spreadspreview import SpreadsPreview


class MangaSpreadFuser(QApplication):  # pylint: disable=too-few-public-methods
    """! MangaSpreadFuser logic.
    """

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()

        self._args = args

        self._right_to_left = self._args.left_to_right is None or not self._args.left_to_right
        self._start_index = self._args.start_index
        self._overwrite = self._args.overwrite
        self._mode = self._args.mode
        self._renumber = self._args.renumber
        self._min_width = self._args.min_width

    def run(self) -> int:
        """! Run the main logic.
        """
        for file in self._args.files:
            self._process_cbz(file)

        return 0

    def _process_cbz(self, file: Path) -> None:
        print(f"Opening {file}...")

        try:
            with CBZ(file) as cbz:
                spread_candidates_list: list[list[dict[str, Any]]] = []

                spread_candidates = self._collect_spread_candidates(cbz, self._start_index)
                if len(spread_candidates) > 0:
                    spread_candidates_list.append(spread_candidates)

                spread_candidates = self._collect_spread_candidates(cbz, self._start_index + 1)
                if len(spread_candidates) > 0:
                    spread_candidates_list.append(spread_candidates)

                if len(spread_candidates_list) == 0:
                    print(f"No spread candidates in {file}...")
                    return

                spread_candidate_set: dict[str, Any] = {
                    "set_index": 0,
                    "candidates": spread_candidates_list
                }

                dlg = SpreadsPreview(str(file), spread_candidate_set)
                if dlg.exec() != 1:
                    print(f"Skipping {file}...")
                    return

                candidates = spread_candidate_set["candidates"][spread_candidate_set["set_index"]]
                spreads = list(filter(lambda c: c["is_spread"], candidates))
                print(f"{len(spreads)} confirmed spread{"" if len(spreads) == 1 else "s"} in {file}")

                if len(spreads) == 0:
                    return

                self._write_fused_images(cbz, spreads)

        except UnidentifiedImageError as err:
            raise RuntimeError(f"Failed to read image: {err}") from err
        except (TypeError, ValueError, FileNotFoundError, PermissionError, OSError) as err:
            raise RuntimeError(f"Failed to open CBZ: {err}") from err

    def _collect_spread_candidates(self, cbz: CBZ, start_index) -> list[dict[str, Any]]:
        spread_candidates: list[dict[str, Any]] = []

        pages = cbz.get_page_names()

        for i in range(start_index, len(pages), 2):
            if i == len(pages) - 1:
                continue

            page_l = pages[i]
            page_r = pages[i + 1]

            suffix = Path(page_l).suffix if Path(page_l).suffix == Path(page_r).suffix else ".png"
            if self._mode in ("add_before", "replace"):
                fused_name = Path(page_l).parent / (Path(page_l).stem + "#fused" + suffix)
            elif self._mode in ("add_middle", ):
                fused_name = Path(page_l).parent / (Path(page_l).stem + "_fused" + suffix)
            elif self._mode in ("add_after", ):
                fused_name = Path(page_r).parent / (Path(page_r).stem + "_fused" + suffix)
            else:
                fused_name = Path(page_r).parent / (Path(page_r).stem + "_fused" + suffix)

            if not self._right_to_left:
                page_l, page_r = page_r, page_l

            with cbz.get_page(page_l) as image_l, cbz.get_page(page_r) as image_r:
                is_spread_candate, preview = self._is_spread_candidate(image_l, image_r)

            if not is_spread_candate or preview is None:
                continue

            spread_candidates.append({
                "page_l": page_l,
                "page_r": page_r,
                "preview": preview,
                "is_spread": False,
                "fused_name": fused_name,
                "fused": None,
            })

        return spread_candidates

    @staticmethod
    def _is_spread_candidate(image_l: Image.Image, image_r: Image.Image) -> tuple[bool, Image.Image | None]:
        size_l = image_l.size
        size_r = image_r.size

        preview_crop_l = image_l.crop((0, 0, 0.2 * size_l[0], size_l[1]))
        calculation_crop_l = image_l.crop((0.01 * size_l[0], 0,
                                           0.04 * size_l[0], size_l[1])).convert('1', dither=Image.Dither.NONE)

        preview_crop_r = image_r.crop((0.8 * size_r[0], 0, size_r[0], size_r[1]))
        calculation_crop_r = image_r.crop((0.96 * size_r[0], 0,
                                           0.99 * size_r[0], size_r[1])).convert('1', dither=Image.Dither.NONE)

        hist_l = calculation_crop_l.histogram()
        hist_r = calculation_crop_r.histogram()

        if hist_l[0] == 0 or hist_l[-1] == 0 or hist_r[0] == 0 or hist_r[-1] == 0:
            return False, None

        preview = Image.new('RGB', (preview_crop_l.width + preview_crop_r.width, preview_crop_l.height))

        preview.paste(preview_crop_r, (0, 0))
        preview.paste(preview_crop_l, (preview_crop_l.width, 0))

        return True, preview

    @staticmethod
    def _create_fused_images(cbz: CBZ, spreads: list[dict[str, Any]]) -> None:
        for spread in spreads:
            if not spread["is_spread"]:
                continue

            with cbz.get_page(spread["page_l"]) as image_l, cbz.get_page(spread["page_r"]) as image_r:
                mode = image_l.mode if image_l.mode == image_r.mode else "RGB"

                fused = Image.new(mode, (image_l.width + image_r.width, image_l.height))

                fused.paste(image_r, (0, 0))
                fused.paste(image_l, (image_l.width, 0))

                spread["fused"] = fused

    @staticmethod
    def _is_finished_spread(candidate: dict[str, Any]) -> bool:
        return candidate["is_spread"] and candidate["fused"] is not None and \
            candidate["fused_name"] is not None and candidate["fused_name"] != ""

    @staticmethod
    def _create_to_add_filelist(spreads: list[dict[str, Any]]) -> list[tuple[str | Path, bytes]]:
        to_add_filelist: list[tuple[str | Path, bytes]] = []

        for spread in spreads:
            if not MangaSpreadFuser._is_finished_spread(spread):
                continue

            fmt = Image.EXTENSION.get(Path(spread["fused_name"]).suffix, "PNG")

            bytes_io = io.BytesIO()
            spread["fused"].save(bytes_io, format=fmt)

            to_add_filelist.append((Path(spread["fused_name"]), bytes_io.getvalue()))

        return to_add_filelist

    @staticmethod
    def _create_to_delete_filelist(spreads: list[dict[str, Any]]) -> list[str | Path]:
        to_delete_filelist: list[str | Path] = []

        for spread in spreads:
            if not MangaSpreadFuser._is_finished_spread(spread):
                continue

            to_delete_filelist.append(Path(spread["page_l"]))
            to_delete_filelist.append(Path(spread["page_r"]))

        return to_delete_filelist

    @staticmethod
    def _create_to_rename_filelist(cbz: CBZ, spreads: list[dict[str, Any]], to_delete: list[str | Path] | None,
                                   width: int) -> dict[str, str]:

        to_delete_lower = [str(file).lower() for file in to_delete] if to_delete is not None else []

        old_pages = list(filter(lambda f: str(f).lower() not in to_delete_lower, cbz.get_page_names()))
        new_pages = [str(s["fused_name"]) for s in spreads if MangaSpreadFuser._is_finished_spread(s)]

        all_pages = sorted(old_pages + new_pages, key=str.lower)
        width = max(width, len(str(len(all_pages) - 1)))

        to_rename = {page: f"{i:0{width}}{Path(page).suffix}" for i, page in enumerate(all_pages)}

        return to_rename

    def _write_fused_images(self, cbz: CBZ, spreads: list[dict[str, Any]]) -> None:
        print("Creating fused images...")
        self._create_fused_images(cbz, spreads)

        files_to_add = self._create_to_add_filelist(spreads)

        files_to_delete: list[str | Path] | None = None
        if self._mode == "replace":
            files_to_delete = self._create_to_delete_filelist(spreads)

        files_to_rename: dict[str, str] | None = None
        if self._renumber:
            files_to_rename = self._create_to_rename_filelist(cbz, spreads, files_to_delete, self._min_width)
        else:
            if files_to_delete is None:
                files_to_delete = []
            files_to_delete.extend(str(file[0]).lower() for file in files_to_add)

        new_filename = cbz.get_path().parent / (cbz.get_path().stem + "_fused" + cbz.get_path().suffix)
        print(f"Writing to {new_filename}...")

        cbz.rewrite(new_filename,
                    files_to_add=files_to_add,
                    files_to_delete=files_to_delete,
                    files_to_rename=files_to_rename,
                    overwrite=self._overwrite)
