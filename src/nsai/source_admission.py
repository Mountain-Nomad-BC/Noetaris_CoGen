"""Named defective-corpus exclusion; never removes or rewrites source data."""
import os
from pathlib import Path
import stat
import unicodedata


def admit_source_path(value):
    """Check available path provenance before trusted import/index/query work.

    This is an exclusion check, not a path permission grant or content-origin
    attestation. Filesystem callers must still refuse traversal and links.
    """
    try:label=os.fspath(value)
    except (TypeError,ValueError):raise ValueError('Invalid source provenance path') from None
    if not isinstance(label,str) or not label or len(label)>32768 or any(ord(c)<32 for c in label):
        raise ValueError('Invalid source provenance path')
    for component in label.replace('\\','/').split('/'):
        normalized=unicodedata.normalize('NFKC',component).rstrip(' .').casefold()
        if normalized.startswith('nsai_master_corpus'):
            raise ValueError('Defective generated corpus is excluded from trusted source operations; retain for failure analysis')


def admit_filesystem_source(value):
    """Refuse linked/reparse ancestors, including the operator-selected base."""
    admit_source_path(value)
    path=Path(value).absolute()
    for component in (path,*path.parents):
        info=component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise ValueError('Source provenance links and reparse paths are not admitted')
    admit_source_path(path)
    return path


def read_source_bytes(value,maximum):
    if type(maximum) is not int or not 1<=maximum<=32*1024*1024:raise ValueError('Invalid source read budget')
    path=admit_filesystem_source(value);before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size>maximum:raise ValueError('Source exceeds bounded read contract')
    with path.open('rb') as source:raw=source.read(maximum+1)
    after=path.stat()
    identity=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)
    if len(raw)>maximum or len(raw)!=before.st_size or identity(before)!=identity(after):
        raise ValueError('Source changed during bounded read')
    return raw
