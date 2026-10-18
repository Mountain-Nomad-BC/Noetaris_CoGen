"""Pinned local ONNX encoder; CPU only, optional dependencies, no network code."""
import hashlib
import json
from pathlib import Path
import re

PINNED_MODEL_SHA256='6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452'
PINNED_MANIFEST_CANONICAL_SHA256='a0be712c8a813d809da78200cdf1dd0970fbcd304f62211ff20c76e2130ecde7'

class LocalSemanticEncoder:
    def __init__(self,modeldir):
        folder=Path(modeldir)
        manifest_path=folder/'manifest.json'
        if folder.is_symlink() or manifest_path.is_symlink():raise ValueError('Model links not admitted')
        raw=manifest_path.read_bytes()
        if len(raw)>65536:raise ValueError('Oversized model manifest')
        manifest=json.loads(raw)
        canonical=json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
        if hashlib.sha256(canonical).hexdigest()!=PINNED_MANIFEST_CANONICAL_SHA256:
            raise ValueError('Encoder manifest digest mismatch with frozen model custody contract')
        if manifest.get('model_id')!='sentence-transformers/all-MiniLM-L6-v2' or not re.fullmatch('[a-f0-9]{40}',manifest.get('revision','')) or manifest.get('dimension')!=384 or manifest.get('max_sequence_length')!=256:raise ValueError('Unsupported pinned model contract')
        files=manifest.get('files',{})
        if not {'model.onnx','tokenizer.json','config.json','tokenizer_config.json','README.md'}<=set(files):raise ValueError('Incomplete model files')
        for name,digest in files.items():
            if name not in {'model.onnx','tokenizer.json','config.json','tokenizer_config.json','README.md'} or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid model file manifest')
            path=folder/name
            if path.is_symlink() or not path.is_file() or path.stat().st_size>128*1024*1024:raise ValueError('Invalid model file')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Model file digest mismatch')
        # Optional imports occur only after byte integrity checks; no Hub loader.
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        self.session=ort.InferenceSession(str(folder/'model.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        if self.session.get_providers()!=['CPUExecutionProvider']:raise ValueError('CPU-only provider required')
        self.tokenizer=Tokenizer.from_file(str(folder/'tokenizer.json'))
        self.tokenizer.no_truncation();self.tokenizer.no_padding()
        self.np=np
        self.identity=dict(name=manifest['model_id'],model_id=manifest['model_id'],revision=manifest['revision'],dimension=384,
                           sha256=files['model.onnx'],model_sha256=files['model.onnx'],manifest_sha256=hashlib.sha256(raw).hexdigest(),max_sequence_length=256,pooling='token-mean-overlap-compensated-special-mean')
        self.cls=self.tokenizer.token_to_id('[CLS]');self.sep=self.tokenizer.token_to_id('[SEP]');self.pad=self.tokenizer.token_to_id('[PAD]')
        if any(v is None for v in (self.cls,self.sep,self.pad)):raise ValueError('Missing BERT special tokens')

    def encode(self,texts):
        """Return normalized vectors + exact tokenizer/window coverage for each text."""
        if not isinstance(texts,list) or not 1<=len(texts)<=10000:raise ValueError('Invalid encoder batch inventory')
        np=self.np;vectors=[];coverage=[]
        for text in texts:
            if not isinstance(text,str) or not text.strip() or len(text.encode())>128*1024:raise ValueError('Invalid encoder passage')
            tokens=self.tokenizer.encode(text,add_special_tokens=False).ids
            if not tokens or len(tokens)>32768:raise ValueError('Passage token budget exceeded')
            # Every original token contributes exactly once after overlap compensation.
            windows=[]
            for start in range(0,len(tokens),222):
                end=min(start+254,len(tokens));windows.append((start,end))
                if end==len(tokens):break
            counts=np.zeros(len(tokens),dtype=np.int32)
            for start,end in windows:counts[start:end]+=1
            total=np.zeros(384,dtype=np.float64)
            special=np.zeros(384,dtype=np.float64)
            for offset in range(0,len(windows),8):
                batch=windows[offset:offset+8];width=max(end-start+2 for start,end in batch)
                ids=np.full((len(batch),width),self.pad,dtype=np.int64);mask=np.zeros_like(ids)
                for row,(start,end) in enumerate(batch):
                    values=[self.cls]+tokens[start:end]+[self.sep];ids[row,:len(values)]=values;mask[row,:len(values)]=1
                feed={'input_ids':ids,'attention_mask':mask,'token_type_ids':np.zeros_like(ids)}
                feed={item.name:feed[item.name] for item in self.session.get_inputs()}
                hidden=self.session.run(None,feed)[0]
                if hidden.ndim!=3 or hidden.shape[:2]!=ids.shape or hidden.shape[2]!=384 or not np.isfinite(hidden).all():raise ValueError('Unexpected encoder output')
                for row,(start,end) in enumerate(batch):
                    weights=1./counts[start:end]
                    total+=(hidden[row,1:end-start+1,:]*weights[:,None]).sum(axis=0)
                    special+=hidden[row,0,:]+hidden[row,end-start+1,:]
            vector=(total+special/len(windows))/(len(tokens)+2);norm=float(np.linalg.norm(vector))
            if not np.isfinite(norm) or norm<=0:raise ValueError('Invalid embedding norm')
            vectors.append((vector/norm).tolist())
            coverage.append(dict(input_tokens=len(tokens),covered_tokens=int((counts>0).sum()),complete=bool((counts>0).all()),windows=len(windows),max_sequence_length=256,pooling='token-mean-overlap-compensated-special-mean',special_tokens_excluded=False))
        return dict(vectors=vectors,coverage=coverage,model_identity=dict(self.identity))
