"""One explicit owned frontend origin; no wildcard credentialed CORS."""
import os
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from .oauth_providers import public_origin,frontend_origin


class DeploymentCORS:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or not os.getenv('NSAI_FRONTEND_ORIGIN'):
            return await self.app(scope,receive,send)
        try:
            frontend=frontend_origin();api=public_origin()
        except (ValueError,TypeError):
            return await JSONResponse({'detail':'Deployment origin configuration unavailable'},503,
                headers={'Cache-Control':'no-store'})(scope,receive,send)
        if frontend==api:return await self.app(scope,receive,send)
        middleware=CORSMiddleware(self.app,allow_origins=[frontend],allow_credentials=True,
            allow_methods=['GET','HEAD','POST','PUT','PATCH','DELETE'],
            allow_headers=['Content-Type','X-CSRF-Token','X-NSAI-Expected-Actor'],
            expose_headers=['X-Request-ID','Content-Type','Content-Length'],max_age=600)
        return await middleware(scope,receive,send)
