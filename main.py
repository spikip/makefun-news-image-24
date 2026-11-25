#!/usr/bin/env python3
"""Entry program for make.fun bounty news-image-20261124.

The entry image — a dense one-page digest of Tuesday 24 November 2026's world
news — is rendered ahead of time by render.py and stored beside this file as
entry.png. This program's whole job is to deliver those exact bytes to the
grader: it copies entry.png into the output directory ($MAKEFUN_OUTPUT_DIR
when set, otherwise /output), verifying on the way that the file is a whole
PNG within the contest's limits (at most 1 MiB, at most 1024 x 1024).
Standard library only; no network; deterministic — every run writes the
same bytes.
"""
import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
MAX_DIM = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def check_png(path):
    """Return (width, height, size) for a valid PNG, or raise ValueError."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        raise ValueError(f"entry.png is {len(data)} bytes, over the 1 MiB cap")
    if not data.startswith(PNG_MAGIC):
        raise ValueError("entry.png does not start with the PNG signature")
    # IHDR is the first chunk: width and height are big-endian uint32 at 16/20.
    width, height = struct.unpack(">II", data[16:24])
    if width > MAX_DIM or height > MAX_DIM:
        raise ValueError(f"entry.png is {width}x{height}, over the 1024 px cap")
    if not data.endswith(b"IEND\xaeB`\x82"):
        raise ValueError("entry.png is truncated: no IEND chunk")
    return width, height, len(data)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    width, height, size = check_png(src)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, "entry.png")
    shutil.copyfile(src, dst)
    print(f"wrote {dst}: {width}x{height} PNG, {size} bytes")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
