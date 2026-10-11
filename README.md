MangaSpreadFuser
================

MangaSpreadFuser is a script that read manga cbz archives, identifies split spreads
and fuses them together into one single image page. Before any fusing happens, the
candidates for spreads are displayed to the user to confirm in a non-spoilerish way.

The general idea of the spoiler-free confirmation, and in fact the whole dialog, is
lifted from the [Kindle Comic Converter](https://github.com/ciromattia/kcc/). KCC
does a lot more things, though, not all of them what I wanted it to do.

MangaSpreadFuser is released under the terms of the
[GNU Affero General Public License version 3](https://www.gnu.org/licenses/agpl.html)
(or later).


Installation
------------

To install MangaSpreadFuser system-wide, use
```
pip install .
```

To install MangaSpreadFuser for current user only, use
```
pip install --user .
```

To install MangaSpreadFuser in a virtualenv, use
```
pip -m venv env
source env/bin/activate
pip install .
```

Optionally, the included [Makefile](Makefile) can be leveraged to install and
run MangaSpreadFuser from a virtualenv. Please read the [Makefile](Makefile) itself
to understand what it can do.

One example of using the [Makefile](Makefile):

```
PYTHON=python3 make arg="manga.cbz"
```

This would install MangaSpreadFuser into a virtualenv and run it on the file
manga.cbz.


Usage
-----

```
mangaspreadfuser [-h] [-v] [-s START_INDEX] [-r] [-l] [-f] [-m {add_before,add_middle,add_after,replace}] [-n] [-w MIN_WIDTH] [<cbz to process> ...]

MangaSpreadFuser -- Fuse split manga spread pages in CBZ

positional arguments:
  <cbz to process>      A CBZ file to process

options:
  -h, --help            Show this help message and exit
  -v, --version         Print the version and exit
  -s, --start_index START_INDEX
                        Page index to start looking for spreads (default: 0)
  -r, --right-to-left   It's a manga with right-to-left read order (default: True)
  -l, --left-to-right   It's a comic with left-to-right read order (default: False)
  -f, --overwrite       Overwrite existing CBZ files (default: False)
  -m, --mode {add_before,add_middle,add_after,replace}
                        What to do with fused pages (default: add_before)
  -n, --renumber        Renumber the page image files in the CBZ (default: False)
  -w, --min-width MIN_WIDTH
                        Minimum number of digits for a page image filename (default: 4, ie. 0001.jpg)

```
