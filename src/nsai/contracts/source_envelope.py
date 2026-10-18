"""Original NSAI source contract; legacy JSON envelopes remain readable as data."""
from pydantic import BaseModel, ConfigDict, Field

class SourceDocument(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_id:str
    title:str
    text:str
    source_type:str='nsai_local'
    url:None=None
    metadata:dict=Field(default_factory=dict)

class SourceEnvelope(BaseModel):
    model_config=ConfigDict(extra='forbid')
    index_name:str
    version:int=1
    documents:list[SourceDocument]=Field(default_factory=list)
    metadata:dict=Field(default_factory=dict)
    created_at:str|None=None
