# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab:

"""! The spread preview dialog.
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

from typing import Any

from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from util import Util


class SpreadsPreview(QDialog):  # pylint: disable=too-few-public-methods
    """! The spread preview dialog.
    """

    def __init__(self, cbz_file: str, spread_candidate_set: dict[str, Any], height: int = 800):
        super().__init__()

        self._index = 0
        self._candidate_set = spread_candidate_set
        self._height = height

        info: dict[str, Any] = Util.get_project_info()
        self.setWindowTitle(f"{info['name']} {info['version']}")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._preview = QLabel()
        self._status = QLabel()

        layout.addWidget(self._preview)
        layout.addWidget(self._status)

        help_layout = QVBoxLayout()

        file_label = QLabel(f"File: {cbz_file}")
        help_layout.addWidget(file_label)
        self._position = QLabel()
        help_layout.addWidget(self._position)
        help_text = [
            "There's two sets of spread candidates:",
            "- Pages 1+2, 3+4, 5+6, ...",
            "- Pages 2+3, 4+5, 6+7, ...",
            "",
            "Use up/down arrows to change candidate set.",
            "Use left/right arrows to change candidate index within the set.",
            "Use space bar to toggle spread on/off.",
            "Use enter key to finish and apply all confirmed spreads.",
            "Use escape key or close window to cancel and skip this CBZ."
        ]
        help_text_label = QLabel('\n'.join(help_text))
        help_layout.addWidget(help_text_label)

        layout.addLayout(help_layout)

        self._update_preview()

    def _get_position(self) -> tuple[int, int, int, int]:
        set_index = self._candidate_set["set_index"]
        set_count = len(self._candidate_set["candidates"])

        candidates_index = self._index
        candidates_count = len(self._get_candidates())

        return set_index, set_count, candidates_index, candidates_count

    def _get_candidates(self) -> list[dict[str, Any]]:
        return self._candidate_set["candidates"][self._candidate_set["set_index"]]

    def _get_candidate(self) -> dict[str, Any]:
        return self._get_candidates()[self._index]

    def _next_candidates(self) -> None:
        set_index, set_count, _, _ = self._get_position()

        self._index = 0
        self._candidate_set["set_index"] = min(set_index + 1, set_count - 1)

    def _previous_candidates(self) -> None:
        set_index, _, _, _ = self._get_position()

        self._index = 0
        self._candidate_set["set_index"] = max(0, set_index - 1)

    def _next_candidate(self) -> None:
        _, _, candidates_index, candidates_count = self._get_position()

        self._index = min(candidates_index + 1, candidates_count - 1)

    def _previous_candidate(self) -> None:
        _, _, candidates_index, _ = self._get_position()

        self._index = max(0, candidates_index - 1)

    def _update_preview(self):
        candidate = self._get_candidate()

        preview = ImageQt(candidate["preview"])
        pixmap = QPixmap(preview).scaledToHeight(self._height * 0.9)
        self._preview.setPixmap(pixmap)

        status = "spread" if candidate["is_spread"] else "not a spread"
        self._status.setText(status)

        set_index, set_count, candidates_index, candidates_count = self._get_position()
        position = f"Set: {set_index} / {set_count - 1} | Candidate: {candidates_index} / {candidates_count - 1} | " \
            f"{candidate["page_l"]} + {candidate["page_r"]}"
        self._position.setText(position)

    def _toggle_spread(self):
        candidate = self._get_candidate()

        candidate["is_spread"] = not candidate["is_spread"]

    def keyReleaseEvent(self, event):  # pylint: disable=missing-function-docstring,invalid-name
        if isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_Up:
                self._previous_candidates()
                self._update_preview()
            elif event.key() == Qt.Key.Key_Down:
                self._next_candidates()
                self._update_preview()
            elif event.key() == Qt.Key.Key_Left:
                self._previous_candidate()
                self._update_preview()
            elif event.key() == Qt.Key.Key_Right:
                self._next_candidate()
                self._update_preview()
            elif event.key() == Qt.Key.Key_Space:
                self._toggle_spread()
                self._update_preview()
            elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.accept()
            else:
                super().keyReleaseEvent(event)
        else:
            super().keyReleaseEvent(event)
