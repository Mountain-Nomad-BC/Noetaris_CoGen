import {sourceId} from './libraryContracts.js';
export const knowledgeKinds=['all','document','passage','source_span','observation','concept_mention','formula'];
export const nodeId=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const integer=value=>Number.isSafeInteger(value)&&value>=0;
const candidate=value=>value?.state==='candidate'&&value.authority_granted===false;
const source=value=>value&&sourceId(value.document_id)&&typeof value.revision==='string'&&value.revision.length>0&&['source_sha256','artifact_sha256','graph_sha256'].every(key=>nodeId(value[key]));
const sameSource=(a,b)=>['document_id','revision','source_sha256','artifact_sha256','graph_sha256'].every(key=>a?.[key]===b?.[key]);
const item=value=>candidate(value)&&nodeId(value.id)&&knowledgeKinds.slice(1).includes(value.kind)&&typeof value.locator==='string'&&typeof value.excerpt==='string'&&integer(value.omitted_characters)&&(value.page===null||(integer(value.page)&&value.page>0));
function envelope(value,document,offset){
 if(!candidate(value)||!source(value.source)||value.source.document_id!==document||value.offset!==offset||value.limit!==25||typeof value.limitation!=='string')throw new Error('Knowledge identity or navigation contract changed.');
}
function pagination(value,total,count){
 if(!integer(total)||count>25||value.offset>40000||!(value.next_offset===null||(integer(value.next_offset)&&value.next_offset===value.offset+25&&value.next_offset<total)))throw new Error('Unrecognized knowledge pagination.');
 if(count!==Math.min(25,Math.max(0,total-value.offset))||(value.next_offset===null)!==(value.offset+25>=total))throw new Error('Knowledge page is incomplete or inconsistent.');
}
export function knowledgePage(value,{document,offset=0,kind='all'}){
 envelope(value,document,offset);
 if(!Array.isArray(value.items)||value.items.some(row=>!item(row)||!integer(row.relationships)||(kind!=='all'&&row.kind!==kind))||new Set(value.items.map(row=>row.id)).size!==value.items.length)throw new Error('Unrecognized candidate node page.');
 pagination(value,value.total,value.items.length);
 const summary=value.summary;
 if(summary?.node_kinds!==undefined){
  const counts=summary.node_kinds;
  if(!counts||typeof counts!=='object'||Array.isArray(counts)||Object.keys(counts).length!==knowledgeKinds.length-1||knowledgeKinds.slice(1).some(kind=>!integer(counts[kind]))||Object.values(counts).reduce((a,b)=>a+b,0)!==summary.nodes)throw new Error('Unrecognized source organization counts.');
 }
 if(!summary||!['nodes','relationships','formulas'].every(key=>integer(summary[key]))||summary.nodes>10000||summary.relationships>40000||summary.formulas>summary.nodes||typeof summary.source_processing_complete!=='boolean'||summary.formula_detection_exhaustive!==false)throw new Error('Unrecognized extraction coverage.');
 return value;
}
export function knowledgeDetail(value,{document,id,offset=0,expectedSource}){
 envelope(value,document,offset);
 const node=value.node,citation=value.citation;
 if(!sameSource(value.source,expectedSource)||!candidate(node)||node.id!==id||!nodeId(id)||!knowledgeKinds.slice(1).includes(node.kind)||typeof node.text!=='string'||typeof node.locator!=='string'||node.document_id!==document||node.source_sha256!==expectedSource.source_sha256||node.source?.revision!==expectedSource.revision||node.source?.document_id!==document)throw new Error('Knowledge node does not match the selected source artifact.');
 if(!citation||citation.chunk_id!==id||citation.document_id!==document||citation.revision!==expectedSource.revision||citation.original_sha256!==expectedSource.source_sha256||citation.locator!==node.locator||citation.excerpt!==node.text)throw new Error('Knowledge citation does not match its source node.');
 if(citation.anchor&&(citation.anchor.document_id!==document||citation.anchor.original_sha256!==expectedSource.source_sha256||citation.anchor.revision!==expectedSource.revision||citation.anchor.selector?.exact!==node.text))throw new Error('Knowledge quote selector belongs to another source.');
 if(!Array.isArray(value.relationships)||value.relationships.some(edge=>!nodeId(edge.id)||typeof edge.kind!=='string'||!['incoming','outgoing'].includes(edge.direction)||!item(edge.other)||edge.interpretation_verified!==false||edge.authority_granted!==false))throw new Error('Unrecognized candidate relationship.');
 pagination(value,value.total_relationships,value.relationships.length);
 return value;
}
