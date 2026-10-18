import { sourceId } from './libraryContracts.js';
export function analysisRequest(input) {
  const integer = (value, minimum, maximum) => {
    if (!/^\d+$/.test(String(value))) throw new Error('Columns and row skips must be explicit integers.');
    const number = Number(value);
    if (!Number.isSafeInteger(number) || number < minimum || number > maximum) throw new Error('Column or row-skip value is outside its supported range.');
    return number;
  };
  if (!['count', 'sum', 'mean', 'min', 'max'].includes(input.operation)) throw new Error('Unsupported calculation');
  if (typeof input.unit !== 'string' || input.unit.length > 60 || /[\x00-\x1f\x7f]/.test(input.unit)) throw new Error('Unit must be an explicit label of at most 60 characters.');
  return { value_column: integer(input.value, 1, 100), group_column: input.group === '' ? null : integer(input.group, 1, 100),
    skip_rows: integer(input.skip, 0, 10), operation: input.operation, unit: input.unit, sheet: input.sheet || null };
}
export function analysisResult(result, source, request) {
  if (!result || result.schema !== 'nsai.table-analysis/1' || result.method !== 'deterministic-decimal' || result.provenance_complete !== true || result.document_id !== source.id ||
      result.original_sha256 !== source.original_sha256 || result.revision !== source.revision ||
      result.authority_granted !== false || !/^[a-f0-9]{64}$/.test(result.analysis_sha256 || '') ||
      !Array.isArray(result.source_dependencies) || result.source_dependencies.length !== 1 || result.source_dependencies[0] !== source.id ||
      !result.request || Object.entries(request).some(([key,value]) => result.request[key] !== value) ||
      !Array.isArray(result.groups) || result.groups.length > 100 || result.groups.some(row => typeof row.label !== 'string' || typeof row.value !== 'string' || !/^-?\d+(?:\.\d+)?$/.test(row.value) || !Number.isSafeInteger(row.included_records) || row.included_records < 1) ||
      !result.coverage || !['total_records','skipped_records','selected_records','included_records','excluded_records'].every(key => Number.isSafeInteger(result.coverage[key]) && result.coverage[key] >= 0) ||
      !result.unit || result.unit.label !== (request.operation === 'count' ? 'records' : request.unit) || typeof result.numeric_policy !== 'string')
    throw new Error('Calculation result does not match the selected source, revision or request.');
  if (result.coverage.total_records - result.coverage.skipped_records !== result.coverage.selected_records ||
      result.coverage.included_records + result.coverage.excluded_records !== result.coverage.selected_records ||
      result.groups.reduce((sum,row) => sum+row.included_records,0) !== result.coverage.included_records)
    throw new Error('Calculation coverage or group denominators conflict.');
  if (request.sheet !== null && result.worksheet?.name !== request.sheet) throw new Error('Calculation worksheet changed.');
  return result;
}
export function accessSnapshot(value, document, actor) {
  if (!value || value.document_id !== document || !sourceId(document) || value.owner !== actor || !Number.isSafeInteger(value.epoch) || value.epoch < 1 ||
      !Array.isArray(value.grants) || value.grants.some(row => !['user','group'].includes(row.subject_kind) || typeof row.subject_id !== 'string' || typeof row.revoked !== 'boolean' || !(row.expires_at === null || typeof row.expires_at === 'string')))
    throw new Error('Owner sharing state is unavailable or changed.');
  return value;
}
export function shareRequest(snapshot, { kind, target, expiry = '', revoke = false }) {
  const pattern = kind === 'user' ? /^local-user-[a-z][a-z0-9_-]{0,63}$/ : kind === 'group' ? /^[a-z][a-z0-9_-]{0,63}$/ : null;
  if (!pattern || !pattern.test(target)) throw new Error('Enter an exact existing user or group identifier.');
  if (!Number.isSafeInteger(snapshot.epoch) || snapshot.epoch < 1) throw new Error('Reload current sharing state first.');
  let expires_at = null;
  if (expiry && !revoke) {
    const parts = /^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.\d{1,6})?(Z|[+-]\d\d:\d\d)$/.exec(expiry);
    if (!parts || +parts[2] < 1 || +parts[2] > 12 || +parts[3] < 1 || +parts[3] > new Date(Date.UTC(+parts[1],+parts[2],0)).getUTCDate() ||
        +parts[4] > 23 || +parts[5] > 59 || +parts[6] > 59 || !Number.isFinite(Date.parse(expiry)) || Date.parse(expiry) <= Date.now())
      throw new Error('Expiry must be a future ISO timestamp with an explicit timezone.');
    expires_at = expiry;
  }
  return { expected_epoch: snapshot.epoch, subject_kind: kind, subject_id: target, expires_at, revoke };
}
