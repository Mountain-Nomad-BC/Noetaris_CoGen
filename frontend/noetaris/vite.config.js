import { defineConfig, loadEnv } from 'vite';
import { deploymentRequest } from './src/noetaris/services/deploymentOrigin.js';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig(({mode}) => {
  const env=loadEnv(mode,process.cwd(),'VITE_');
  const allowed=new Set(['VITE_NOETARIS_MODE','VITE_API_ORIGIN','VITE_APP_ORIGIN','VITE_DEPLOYMENT_SITE']);
  if(Object.keys(env).some(key=>!allowed.has(key)))throw new Error('Unrecognized public frontend build setting');
  if(env.VITE_API_ORIGIN)deploymentRequest('/auth/config',env,env.VITE_APP_ORIGIN);
  const metadata={mode:env.VITE_NOETARIS_MODE==='demo'?'demo':'live',api_origin:env.VITE_API_ORIGIN||'',app_origin:env.VITE_APP_ORIGIN||'',deployment_site:env.VITE_DEPLOYMENT_SITE||''};
  return {
  plugins: [react(),{name:'public-deployment-metadata',generateBundle(){
    this.emitFile({type:'asset',fileName:'deployment-config.json',source:JSON.stringify(metadata,null,2)+'\n'});
  }}],
  build: { sourcemap: false },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:8790',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://127.0.0.1:8790',
        changeOrigin: true,
      },
      '/healthz': {
        target: 'http://127.0.0.1:8790',
        changeOrigin: true,
      },
      '/readyz': {
        target: 'http://127.0.0.1:8790',
        changeOrigin: true,
      },
    }
  }
  };
});
