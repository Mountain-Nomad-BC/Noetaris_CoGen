import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { apiRequest } from '../../services/api';
import { sourceId, sourceRecord } from '../../services/libraryContracts';
import { boundAnchor, sha256, containedPdfRects } from '../../services/pdfIdentity';
import { loadPdfRuntime, pdfResourceFactory, PDF_BASE } from '../../services/pdfRuntime';
import './pdf-workspace.css';

export default function LivePdfWorkspace() {
  const { id } = useParams();const location=useLocation();
  return <PdfDocument key={id} id={id} anchor={location.state?.anchor || null} />;
}
function PdfDocument({id,anchor}) {
  const [state,setState]=useState({source:null,ready:false,error:null});
  const [page,setPage]=useState(1);const [scale,setScale]=useState(1);const [rotation,setRotation]=useState(0);
  const [status,setStatus]=useState('Loading authorized PDF evidence…');const [retry,setRetry]=useState(0);
  const canvas=useRef(null),text=useRef(null),marks=useRef(null),surface=useRef(null),current=useRef(null);
  const generation=useRef(0);
  useEffect(() => {
    let alive=true,task=null,timer=null;const controller=new AbortController();
    const fonts={failures:new Set(),controllers:new Set()};
    generation.current++;
    setState({source:null,ready:false,error:null});setStatus('Loading authorized PDF evidence…');current.current=null;
    if(canvas.current){canvas.current.width=0;canvas.current.height=0;}
    text.current?.replaceChildren();marks.current?.replaceChildren();
    if(surface.current){surface.current.style.width='0px';surface.current.style.height='0px';}
    (async () => {
      if (!sourceId(id)) throw new Error('Invalid source identifier. No sample PDF is substituted.');
      const source=sourceRecord(await apiRequest(`/v1/sources/${id}`,{signal:controller.signal}),id);
      if (source.media_type!=='application/pdf') throw new Error('This source is not a PDF. Inspect its retained evidence in the library.');
      const payload=await apiRequest(`/v1/sources/${id}/original`,{signal:controller.signal,responseType:'bytes',maximumBytes:25*1024*1024});
      if (await sha256(payload.bytes)!==source.original_sha256) throw new Error('Original PDF integrity check failed. Rendering withheld.');
      if (!alive) return;
      const runtime=await loadPdfRuntime();if(!alive)return;
      task=runtime.renderer.getDocument({data:payload.bytes,BinaryDataFactory:pdfResourceFactory(fonts),useWorkerFetch:false,standardFontDataUrl:PDF_BASE+'pdfjs/standard_fonts/',isEvalSupported:false,useSystemFonts:false,disableFontFace:true,disableAutoFetch:true,disableStream:true,enableXfa:false,maxImageSize:16000000,isOffscreenCanvasSupported:false});
      const pdf=await Promise.race([task.promise,new Promise((_,reject)=>{timer=setTimeout(()=>{task.destroy().catch(()=>{});reject(new Error('PDF loading exceeded 30 seconds.'));},30000);})]).finally(()=>clearTimeout(timer));
      if(!alive)return;
      if(pdf.numPages>1000)throw new Error('PDF exceeds the viewer page budget.');
      let quote=null,warning='';
      try { quote=await boundAnchor(anchor,source,pdf.numPages); }
      catch(error) { warning=error.message+' No passage highlight is inferred.'; }
      if(!alive)return;
      current.current={pdf,runtime,fonts,source,quote,warning};setPage(quote?.page||1);setScale(1);setRotation(0);
      setState({source,ready:true,error:null});
    })().catch(error=>{
      task?.destroy().catch(()=>{});for(const item of fonts.controllers)item.abort();
      if(alive && error.name!=='AbortError'){setState({source:null,ready:false,error:error.message});setStatus('PDF unavailable; no original rendered.');}
    });
    return ()=>{alive=false;controller.abort();clearTimeout(timer);for(const item of fonts.controllers)item.abort();task?.destroy().catch(()=>{});current.current=null;};
  },[id,anchor,retry]);
  useEffect(()=>{
    if(!state.ready||!current.current)return;
    let alive=true,render=null,layer=null;const owner=current.current;const version=++generation.current;
    const valid=()=>alive&&version===generation.current&&current.current===owner;
    const element=canvas.current;
    // PDF.js tasks own fresh containers so a cancelled task cannot mutate a newer layer.
    const textLayer=document.createElement('div');textLayer.className='pdf-text-layer';
    const quoteLayer=document.createElement('div');quoteLayer.className='nsai-pdf-quotes';
    text.current.replaceChildren(textLayer);marks.current.replaceChildren(quoteLayer);
    element.width=0;element.height=0;surface.current.style.width='0px';surface.current.style.height='0px';
    setStatus('Rendering selected page; no passage highlighted.');
    (async()=>{
      const item=await owner.pdf.getPage(page);if(!valid())return;
      const viewport=item.getViewport({scale,rotation:(item.rotate+rotation)%360});
      const geometry=owner.runtime.canvasGeometry(viewport.width,viewport.height,window.devicePixelRatio);
      element.width=geometry.pixelWidth;element.height=geometry.pixelHeight;element.style.width=geometry.width+'px';element.style.height=geometry.height+'px';
      surface.current.style.width=geometry.width+'px';surface.current.style.height=geometry.height+'px';
      render=item.render({canvasContext:element.getContext('2d'),viewport,transform:geometry.transform,annotationMode:0});await render.promise;if(!valid())return;
      const content=await item.getTextContent();if(!valid())return;
      const strings=content.items.filter(item=>typeof item.str==='string');let message='Page view only; no citation passage selected.';
      if(strings.length<=10000 && strings.reduce((sum,item)=>sum+item.str.length,0)<=64000){
        textLayer.style.setProperty('--total-scale-factor',scale);
        layer=new owner.runtime.renderer.TextLayer({textContentSource:content,container:textLayer,viewport});await layer.render();if(!valid())return;
        if(owner.fonts.failures.size)message='A local PDF resource is unavailable. Passage highlighting is withheld.';
        else if(owner.quote?.page===page){
          const matched=owner.runtime.highlightQuote(layer,owner.quote.selector.exact,quoteLayer);
          message=matched==='unique'?'Unique native text match highlighted; interpretation remains unverified.':matched==='ambiguous'?'Quote is duplicated on this page. No guessed highlight.':'Quote cannot be uniquely aligned; page shown without a highlight.';
          if(matched==='not-found'){
            const metadata=owner.source.manifest?.documents?.[0]?.metadata||owner.source.manifest?.metadata;
            const coverage=metadata?.pages?.find(record=>record.page===page);
            if(coverage?.status==='ocr'&&coverage.complete===true){
              const ocr=owner.runtime.highlightOcrQuote(metadata.ocr_words,owner.quote.selector.exact,viewport,quoteLayer,page);
              message=ocr==='unique'?'Unique OCR word regions highlighted; recognition and interpretation remain unverified.':'OCR quote or coordinate custody cannot be uniquely aligned; no guessed highlight.';
            }
          }
        }
      }else message='Text exceeds the alignment budget; no passage highlight.';
      if(quoteLayer.childElementCount && !containedPdfRects(surface.current.getBoundingClientRect(),[...quoteLayer.children].map(mark=>mark.getBoundingClientRect()))){
        quoteLayer.replaceChildren();message='Quote regions lie outside the visible page; no passage highlight is inferred.';
      }
      if(valid())setStatus(`Page ${page}/${owner.pdf.numPages}. ${owner.warning||message} Viewing a citation does not change chat scope.`);
    })().catch(error=>{if(valid() && error.name!=='RenderingCancelledException')setStatus('Page rendering failed: '+error.message);});
    return()=>{alive=false;generation.current++;render?.cancel();layer?.cancel();};
  },[state.ready,page,scale,rotation]);
  return <section className="p-4 md:p-8 space-y-4 min-w-0" data-testid="live-pdf-workspace">
    <h1 className="font-display text-2xl">Source PDF workspace</h1>
    <Link to="/app/library">Back to library</Link>
    {state.error&&<p role="alert">{state.error}</p>}
    <button className="n-btn-ghost p-2" onClick={()=>setRetry(value=>value+1)}>Reload authorized source</button>
    {state.source&&<><h2>{state.source.title}</h2><p className="break-all">Revision {state.source.revision} · original SHA-256 {state.source.original_sha256}</p></>}
    {state.ready&&<div className="flex flex-wrap gap-3 items-center">
      <button disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous page</button>
      <label>Page<select aria-label="PDF page" className="n-glass p-2" value={page} onChange={event=>setPage(Number(event.target.value))}>{Array.from({length:current.current?.pdf.numPages||0},(_,index)=><option key={index+1}>{index+1}</option>)}</select></label>
      <button disabled={page>=(current.current?.pdf.numPages||0)} onClick={()=>setPage(value=>value+1)}>Next page</button>
      <label>Zoom<select aria-label="PDF zoom" className="n-glass p-2" value={scale} onChange={event=>setScale(Number(event.target.value))}>{[0.5,0.75,1,1.25,1.5,2].map(value=><option key={value} value={value}>{value*100}%</option>)}</select></label>
      <label>Rotation<select aria-label="PDF rotation" className="n-glass p-2" value={rotation} onChange={event=>setRotation(Number(event.target.value))}>{[0,90,180,270].map(value=><option key={value}>{value}</option>)}</select></label>
    </div>}
    <p role="status" data-testid="pdf-render-status">{status}</p>
    <p>No PDF links, forms, attachments or active actions are enabled. Extraction availability, OCR accuracy and interpretation require separate evidence.</p>
    <div className="overflow-auto max-w-full n-panel rounded" data-testid="pdf-scroll-surface"><div ref={surface} className="nsai-pdf-surface"><canvas ref={canvas} data-testid="live-pdf-canvas" /><div ref={text} className="nsai-pdf-text-host" data-testid="live-pdf-text" /><div ref={marks} className="nsai-pdf-quotes" data-testid="live-pdf-quotes" /></div></div>
  </section>;
}
