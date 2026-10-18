import test from 'node:test';
import assert from 'node:assert/strict';
import {knowledgePage,knowledgeDetail} from '../src/noetaris/services/knowledgeContracts.js';
const document='a'.repeat(32),id='b'.repeat(64),other='c'.repeat(64);
const source=()=>({document_id:document,revision:'1',source_sha256:'d'.repeat(64),artifact_sha256:'e'.repeat(64),graph_sha256:'f'.repeat(64)});
const item=()=>({id,kind:'source_span',locator:'line:1',excerpt:'Quoted source.',page:null,omitted_characters:0,state:'candidate',authority_granted:false});
const page=()=>({source:source(),items:[{...item(),relationships:1}],total:1,offset:0,limit:25,next_offset:null,summary:{nodes:1,relationships:1,formulas:0,source_processing_complete:true,formula_detection_exhaustive:false},state:'candidate',authority_granted:false,limitation:'Candidate only'});
const detail=()=>({source:source(),node:{id,kind:'source_span',locator:'line:1',text:'Quoted source.',document_id:document,source_sha256:source().source_sha256,source:source(),state:'candidate',authority_granted:false},citation:{chunk_id:id,document_id:document,revision:'1',original_sha256:source().source_sha256,locator:'line:1',excerpt:'Quoted source.'},relationships:[{id:'1'.repeat(64),kind:'derived_from_text',direction:'outgoing',other:{...item(),id:other},interpretation_verified:false,authority_granted:false}],total_relationships:1,offset:0,limit:25,next_offset:null,state:'candidate',authority_granted:false,limitation:'Candidate only'});
const args=()=>({document,id,expectedSource:source()});
test('source-bound candidate pages and relationship details are accepted',()=>{assert.equal(knowledgePage(page(),{document}).total,1);assert.equal(knowledgeDetail(detail(),args()).node.text,'Quoted source.');});
test('foreign source, factual authority and exhaustive formula assertions are rejected',()=>{for(const mutate of [v=>v.source.document_id='0'.repeat(32),v=>v.authority_granted=true,v=>v.items[0].state='verified',v=>v.summary.formula_detection_exhaustive=true]){const v=page();mutate(v);assert.throws(()=>knowledgePage(v,{document}));}});
test('missing rows, duplicate identities and invented page offsets fail closed',()=>{for(const mutate of [v=>v.total=2,v=>v.items.push(v.items[0]),v=>v.next_offset=1]){const v=page();mutate(v);assert.throws(()=>knowledgePage(v,{document}));}});
test('mixed artifact revisions, quote bytes and relationship authority are rejected',()=>{for(const mutate of [v=>v.source.graph_sha256='9'.repeat(64),v=>v.node.source.revision='2',v=>v.citation.excerpt='Other text',v=>v.relationships[0].interpretation_verified=true,v=>v.relationships[0].other.authority_granted=true]){const v=detail();mutate(v);assert.throws(()=>knowledgeDetail(v,args()));}});
test('full retained formula text is preserved without evaluation',()=>{const v=detail(),text='E = '+ 'x'.repeat(16000);v.node.kind='formula';v.node.text=text;v.node.formula_data={evaluation:'not_attempted',expression:text};v.citation.excerpt=text;assert.equal(knowledgeDetail(v,args()).node.formula_data.expression,text);});
test('last and empty pages preserve explicit navigation bounds',()=>{const v=page();v.offset=25;v.items=[];assert.equal(knowledgePage(v,{document,offset:25}).next_offset,null);});

test('automatic source groups require every supported kind and exact total',()=>{
 const v=page();v.summary.node_kinds={document:0,passage:0,source_span:1,observation:0,concept_mention:0,formula:0};
 assert.equal(knowledgePage(v,{document}).summary.node_kinds.source_span,1);
 for(const mutate of [x=>x.summary.node_kinds.formula=-1,x=>x.summary.node_kinds.source_span=2,x=>delete x.summary.node_kinds.document,x=>x.summary.node_kinds.fake=0]){
  const bad=structuredClone(v);mutate(bad);assert.throws(()=>knowledgePage(bad,{document}));
 }
});


import {librarySearchResult} from '../src/noetaris/services/libraryContracts.js';
test('library content results require real source identities and omit unrequested fields',()=>{
 const value={items:[{id:'a'.repeat(32),document_id:'b'.repeat(32),title:'Uploaded source',revision:'1',locator:'line:2',text:'Source observation',secret:'PRIVATE_SENTINEL'}],retrieval_coverage:{method:'authorized-lexical-semantic-rank-fusion',semantic_state:'ready'}};
 assert.equal(librarySearchResult(value).items[0].document_id,'b'.repeat(32));assert.doesNotMatch(JSON.stringify(librarySearchResult(value)),/PRIVATE_SENTINEL/);
 for(const mutate of [v=>v.items[0].document_id='foreign',v=>v.items.push(v.items[0]),v=>v.retrieval_coverage.semantic_state='assumed-ready']){const bad=structuredClone(value);mutate(bad);assert.throws(()=>librarySearchResult(bad));}
});
