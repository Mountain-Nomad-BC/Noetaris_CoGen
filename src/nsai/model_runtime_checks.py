"""Actual private model auth checks; never prints credentials."""
import json
import httpx
from .inference import model_settings
base,model,key=model_settings()
with httpx.Client(timeout=5,trust_env=False) as client:
    denied=client.get(base+'/models')
    accepted=client.get(base+'/models',headers={'Authorization':'Bearer '+key})
assert denied.status_code==401 and accepted.status_code==200
assert any(item['id']==model for item in accepted.json()['data'])
print(json.dumps(dict(status='PASS',model=model,unauthenticated_model_request=401,
    authenticated_model_request=200,credentials_logged=False,provider='local-llamacpp-cpu'),indent=2))
