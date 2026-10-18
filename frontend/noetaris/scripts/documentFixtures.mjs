// Original synthetic documents for the owned local browser qualification.
export function documentFixture(kind,id){
 const reference='reference'+id.replaceAll('-','');
 const statement='The Aurora laboratory replaces the ceramic membrane every 47 days.';
 if(kind==='csv')return {name:`aurora-guide-${id}.csv`,mimeType:'text/csv',buffer:Buffer.from(`System,IntervalDays,Run\nAurora laboratory ceramic membrane,47,${reference}\n`)};
 if(kind==='pdf'){
  const lines=['Aurora laboratory maintenance guide',statement,'A technician isolates the water supply before replacement.',reference];
  const stream='BT /F1 12 Tf 72 720 Td '+lines.map((text,i)=>(i?'0 -30 Td ':'')+'('+text+') Tj').join(' ')+' ET';
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>','<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>','<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',`<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`];
  let pdf='%PDF-1.4\n';const offsets=[0];
  objects.forEach((value,index)=>{offsets.push(Buffer.byteLength(pdf));pdf+=`${index+1} 0 obj\n${value}\nendobj\n`;});
  const xref=Buffer.byteLength(pdf);pdf+='xref\n0 6\n0000000000 65535 f \n'+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+`trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return {name:`aurora-guide-${id}.pdf`,mimeType:'application/pdf',buffer:Buffer.from(pdf)};
 }
 if(kind!=='markdown')throw new Error('Unsupported browser fixture kind');
 return {name:`aurora-guide-${id}.md`,mimeType:'text/markdown',buffer:Buffer.from(`# Aurora laboratory operating guide ${reference}\n\n## Water purification\n\nThe Aurora laboratory water purification system uses a ceramic membrane. ${statement}\n\n## Maintenance procedure\n\nA technician isolates the water supply before replacing the ceramic membrane. The procedure is recorded in the maintenance register.\n`)};
}
