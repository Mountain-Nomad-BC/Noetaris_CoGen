function httpsOrigin(raw){
  if(typeof raw!=='string'||raw.length>250||!/^[\x21-\x7e]+$/.test(raw)||/[\\%]/.test(raw)||!/^https:\/\/[^/?#]+$/.test(raw))
    throw new Error('Deployment requires an explicit HTTPS origin');
  const url=new URL(raw);
  if(url.protocol!=='https:'||url.username||url.password||!url.hostname||
     !/^[a-z0-9.-]+$/i.test(url.hostname)||url.hostname.split('.').some(p=>!p||p.length>63||p.startsWith('-')||p.endsWith('-')))
    throw new Error('Invalid deployment origin');
  return url.origin;
}

export function deploymentRequest(path,settings={},browserOrigin=globalThis.location?.origin){
  if(!settings.VITE_API_ORIGIN)return {url:path,credentials:'same-origin',crossOrigin:false};
  const api=httpsOrigin(settings.VITE_API_ORIGIN),app=httpsOrigin(settings.VITE_APP_ORIGIN);
  if(browserOrigin!==app)throw new Error('This build is bound to a different application origin');
  if(api!==app){
    const site=settings.VITE_DEPLOYMENT_SITE;
    if(typeof site!=='string'||!/^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/.test(site)||!site.includes('.')||
       new URL(api).hostname!=='api.'+site||!['app.'+site,site].includes(new URL(app).hostname))
      throw new Error('Cross-site hosting requires separate cookie and identity review');
  }
  return {url:api+path,credentials:'include',crossOrigin:api!==app};
}
