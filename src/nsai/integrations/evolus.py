"""Small Evolus API adapter for configured workflow executions.

Payload JSON schema must be confirmed in user's Evolus event workspace before
real execution. This file is not wired to public routes or enabled by default.
"""
from __future__ import annotations
import re
import json
import httpx
from ..store import _secret
from ..assembly import strict_json
from ..inference import _bounded_json
from .configuration import evolus_api_base,evolus_configuration

WORKFLOW_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

class EvolusClient:
    def __init__(self, *, key_file: str, application_id: str, workflow_id: str, api_base: str):
        if not isinstance(application_id,str) or not WORKFLOW_ID.fullmatch(application_id):
            raise ValueError("Invalid Evolus application ID")
        if not isinstance(workflow_id,str) or not WORKFLOW_ID.fullmatch(workflow_id):
            raise ValueError('Invalid configured Evolus workflow ID')
        self.application_id = application_id
        self.workflow_id = workflow_id
        self.api_base = evolus_api_base(api_base)
        self.key_file = key_file

    @classmethod
    def from_configuration(cls, *, config_file, key_file):
        data=evolus_configuration(config_file)
        return cls(key_file=key_file,application_id=data['application_id'],
                   workflow_id=data['workflow_id'],api_base=data['api_base'])

    async def execute_workflow(self, workflow_id: str, payload: dict) -> dict:
        if not isinstance(workflow_id,str) or not WORKFLOW_ID.fullmatch(workflow_id) or workflow_id!=self.workflow_id:
            raise ValueError("Invalid workflow ID")
        if not isinstance(payload,dict):
            raise ValueError('Evolus workflow input must be an object')
        try:
            raw=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
            strict_json(raw,max_bytes=262144,max_depth=16,max_items=10000)
        except (ValueError,TypeError):
            raise ValueError('Invalid or oversized Evolus workflow input') from None
        try:key=_secret(self.key_file)
        except (OSError,RuntimeError,UnicodeError):
            raise RuntimeError('Evolus credential unavailable') from None
        if not key.isascii() or not 16<=len(key)<=1024 or any(ord(c)<=32 for c in key):
            raise RuntimeError('Invalid Evolus credential')
        async with httpx.AsyncClient(timeout=30, follow_redirects=False,trust_env=False) as client:
            result = await _bounded_json(client,'POST',
                f"{self.api_base}/workflows/{workflow_id}/execute",
                headers={"X-ApiKey": key, "X-Application-Id": self.application_id},
                payload=payload,maximum=1048576,deadline=30,
            )
            if not isinstance(result,dict):
                raise RuntimeError('Invalid Evolus workflow response')
            return result
