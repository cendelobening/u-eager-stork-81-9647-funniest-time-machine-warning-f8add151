"""Funniest Time Machine Warning Label — make.fun entry.

Writes a single one-line warning label for a time machine to
``<MAKEFUN_OUTPUT_DIR>/entry.txt`` (default ``/output/entry.txt``).

Pure Python standard library only.
"""

import os
import stat
import sys
import tempfile

# The entry: one warning label, at most 120 characters.
# Beat 1 states the paradox, beat 2 twists it, beat 3 lands on the reader.
ENTRY_LINE = "WARNING: Your past self read this label and ignored it. So will you."

MAX_CHARS = 120


def validate(line):
    """Check the entry line meets the gate before anything is written."""
    if not isinstance(line, str):
        raise ValueError("entry must be a string")
    if not line:
        raise ValueError("entry must not be empty")
    if line.strip() == "":
        raise ValueError("entry must not be whitespace only")
    if len(line) > MAX_CHARS:
        raise ValueError("entry is %d chars, over the 120 limit" % len(line))
    if "\n" in line or "\r" in line:
        raise ValueError("entry must be a single line")
    if len(line.splitlines()) != 1:
        raise ValueError("entry must be exactly one line")
    if line != line.strip():
        raise ValueError("entry must not have leading/trailing whitespace")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in line):
        raise ValueError("entry must not contain control characters")
    if not any(ch.isalpha() for ch in line):
        raise ValueError("entry must contain at least one letter")
    return line


def main():
    line = validate(ENTRY_LINE)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")

    data = line.encode("utf-8")

    # Write via a temp file in the same directory, then atomically replace.
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".entry-", suffix=".tmp")
    try:
        os.write(fd, data)
        os.fsync(fd)
        os.close(fd)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, out_path)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    os.chmod(out_path, 0o644)

    # Read back and verify: exact bytes, valid UTF-8, no trailing newline.
    with open(out_path, "rb") as fh:
        raw = fh.read()
    if raw != data:
        raise SystemExit("verification failed: bytes on disk differ from entry")
    text = raw.decode("utf-8")
    if text != line:
        raise SystemExit("verification failed: decoded text differs from entry")
    if raw.endswith(b"\n"):
        raise SystemExit("verification failed: trailing newline present")
    mode = stat.S_IMODE(os.stat(out_path).st_mode)
    if mode != 0o644:
        raise SystemExit("verification failed: mode is %o, expected 0644" % mode)

    print("wrote %s (%d chars)" % (out_path, len(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
