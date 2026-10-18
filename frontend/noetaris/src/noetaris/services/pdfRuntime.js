import { PDF_FONT_HASHES } from './pdfFontHashes';
import { sha256 } from './pdfIdentity';
export const PDF_BASE = '/pdf-runtime/';
let pending;
const publicModule = path => import(/* @vite-ignore */ path);
export async function loadPdfRuntime() {
  if (!pending) pending = Promise.all([
    publicModule('/pdf-runtime/pdfjs/pdf.mjs'),
    publicModule('/pdf-runtime/pdf-canvas.mjs'),
    publicModule('/pdf-runtime/pdf-quotes.mjs'),
  ]).then(([renderer,canvas,quotes]) => {
    if (renderer.version !== '6.4.299') throw new Error('PDF runtime version is not qualified.');
    renderer.GlobalWorkerOptions.workerSrc = PDF_BASE+'pdfjs/pdf.worker.mjs';
    return { renderer, ...canvas, ...quotes };
  }).catch(error => { pending = null; throw error; });
  return pending;
}
export function pdfResourceFactory(state) {
  return class {
    async fetch({kind,filename}) {
      const controller = new AbortController(); const timer = setTimeout(() => controller.abort(),5000);
      state.controllers.add(controller);
      try {
        if (kind !== 'standardFontDataUrl' || typeof filename !== 'string' || !Object.hasOwn(PDF_FONT_HASHES,filename)) throw new Error('Unsupported local PDF resource');
        const response = await fetch(PDF_BASE+'pdfjs/standard_fonts/'+filename,{credentials:'omit',cache:'no-store',redirect:'error',signal:controller.signal});
        if (!response.ok || Number(response.headers.get('content-length'))>262144) throw new Error('Local PDF font unavailable or oversized');
        const reader=response.body.getReader();const parts=[];let size=0;
        try { while (true) { const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>262144){controller.abort();throw new Error('PDF font exceeds budget');}parts.push(value); } }
        finally { reader.releaseLock(); }
        const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}
        if (await sha256(bytes)!==PDF_FONT_HASHES[filename] || controller.signal.aborted) throw new Error('Local PDF font integrity check failed');
        return bytes;
      } catch(error) { state.failures.add(kind);throw error; }
      finally { clearTimeout(timer);state.controllers.delete(controller); }
    }
  };
}
