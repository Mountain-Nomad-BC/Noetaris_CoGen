"""Immutable startup upload profiles; evaluation does not grant release acceptance."""
from dataclasses import dataclass, asdict
import os

@dataclass(frozen=True)
class UploadLimits:
    profile: str
    max_bytes: int
    max_pages: int
    max_chars: int = 200_000

    @property
    def base64_chars(self):
        return 4 * ((self.max_bytes + 2) // 3)

    @property
    def request_bytes(self):
        return self.base64_chars + 4096

    def metadata(self):
        return asdict(self)


def select_profile(profile='default'):
    if profile == 'default':
        return UploadLimits(profile, 2 * 1024 * 1024, 100)
    if profile == 'standard-evaluation':
        return UploadLimits(profile, 25 * 1024 * 1024, 250)
    raise ValueError('Invalid server upload profile')

ACTIVE = select_profile(os.getenv('NSAI_UPLOAD_PROFILE', 'default'))
