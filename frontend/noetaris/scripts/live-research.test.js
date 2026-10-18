import test from 'node:test';
import assert from 'node:assert/strict';
import {retrievalCoverageNotice} from '../src/noetaris/services/researchContracts.js';

test('bounded search omissions are visible with truthful lower bounds',()=>{
  assert.equal(retrievalCoverageNotice({
    additional_matches_exist:true,
    matching_chunks_lower_bound:25,
    returned_chunks:12,
    omitted_chunks_at_least:13,
  }),'At least 25 matching chunks; 12 shown and at least 13 omitted. Results are not exhaustive.');
});

test('invalid omission counts do not produce fabricated numbers',()=>{
  assert.equal(retrievalCoverageNotice({
    additional_matches_exist:true,
    matching_chunks_lower_bound:'25',
    returned_chunks:12,
    omitted_chunks_at_least:-1,
  }),'Additional matching excerpts were omitted. Results are not exhaustive.');
});

test('semantic fallback is disclosed and complete lexical results stay quiet',()=>{
  assert.equal(retrievalCoverageNotice({
    semantic_state:'unavailable',
    additional_matches_exist:false,
  }),'Semantic retrieval is unavailable; these results use lexical matching only.');
  assert.equal(retrievalCoverageNotice({
    semantic_state:'ready',
    additional_matches_exist:false,
  }),null);
});
