"""Bounded server profiles; larger reference measurements are not release acceptance.

Default admission stays 100 documents / 2,000 claims / 128 MiB semantic JSON.
The reference profile is selected explicitly by an isolated qualification operator.
Upload byte/page limits and private HTTP admission are independent and unchanged.
"""
import os

PROFILES={'default':dict(documents=100,claims=2000,semantic_payload_bytes=128*1024*1024),
          'reference-1000':dict(documents=1000,claims=2000,semantic_payload_bytes=512*1024*1024)}


def capacity_profile():
    profile=os.getenv('NSAI_CAPACITY_PROFILE','default')
    if profile not in PROFILES:raise ValueError('Invalid server capacity profile')
    return profile


def capacity_limits():return dict(PROFILES[capacity_profile()])
