// Conservative native-text matching. Only whitespace is normalized; duplicated
// or missing text never receives a guessed visual position.
export function uniqueQuote(strings,quote){
  if(!Array.isArray(strings)||strings.length>10000||typeof quote!=='string'||!quote.trim()||quote.length>64000)return {status:'unsupported'};
  let text='',positions=[];
  function add(character,position){if(/\s/u.test(character)){if(text&&!text.endsWith(' ')){text+=' ';positions.push(position);}}else{text+=character;positions.push(position);}}
  for(let item=0;item<strings.length;item++){
    if(typeof strings[item]!=='string')return {status:'unsupported'};
    if(item)add(' ',null);
    for(let offset=0;offset<strings[item].length;offset++){add(strings[item][offset],{item,offset});if(text.length>64000)return {status:'unsupported'};}
  }
  const exact=quote.replace(/\s+/gu,' ').trim(),start=text.indexOf(exact);
  if(start<0)return {status:'not-found'};
  if(text.indexOf(exact,start+1)>=0)return {status:'ambiguous'};
  const first=positions[start],last=positions[start+exact.length-1];
  return first&&last?{status:'unique',start:first,end:{item:last.item,offset:last.offset+1}}:{status:'unsupported'};
}

export function highlightQuote(layer,quote,container){
  container.replaceChildren();
  const match=uniqueQuote(layer.textContentItemsStr,quote);
  if(match.status!=='unique')return match.status;
  const first=layer.textDivs[match.start.item]?.firstChild,last=layer.textDivs[match.end.item]?.firstChild;
  if(first?.nodeType!==3||last?.nodeType!==3)return 'unsupported';
  const range=document.createRange();range.setStart(first,match.start.offset);range.setEnd(last,match.end.offset);
  const parent=container.getBoundingClientRect(),rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
  if(!rects.length||rects.length>1000)return 'unsupported';
  for(const rect of rects){const mark=document.createElement('span');mark.className='pdf-quote-mark';mark.style.left=`${rect.left-parent.left}px`;mark.style.top=`${rect.top-parent.top}px`;mark.style.width=`${rect.width}px`;mark.style.height=`${rect.height}px`;container.append(mark);}
  return 'unique';
}

export function highlightOcrQuote(words,quote,viewport,container,page){
  container.replaceChildren();
  if(!Array.isArray(words)||words.length>50000||!Number.isInteger(page)||page<1||
     !Array.isArray(viewport?.viewBox)||viewport.viewBox.length!==4||
     !viewport.viewBox.every(Number.isFinite)||typeof viewport.convertToViewportPoint!=='function')return 'unsupported';
  const selected=words.filter(word=>word?.page===page),bounds=viewport.viewBox;
  if(!selected.length)return 'not-found';
  const vector=(value,length)=>Array.isArray(value)&&value.length===length&&value.every(Number.isFinite);
  for(const word of selected){
    if(typeof word.text!=='string'||!word.text.trim()||word.text.length>200||
       !Number.isFinite(word.engine_score)||word.engine_score<0||word.engine_score>100||word.engine_score_is_probability!==false||
       !vector(word.pdf_box,4)||!vector(word.pixel_box,4)||!vector(word.pixel_to_pdf,6))return 'unsupported';
    const [x0,y0,x1,y1]=word.pdf_box,[px0,py0,px1,py1]=word.pixel_box,[a,b,c,d,e,f]=word.pixel_to_pdf;
    if(!(bounds[0]<=x0&&x0<x1&&x1<=bounds[2]&&bounds[1]<=y0&&y0<y1&&y1<=bounds[3])||
       !(0<=px0&&px0<px1&&px1<=20000&&0<=py0&&py0<py1&&py1<=20000&&px1*py1<=12000000)||
       Math.abs(e)>40000||Math.abs(f)>40000)return 'unsupported';
    const scale=72/300,matrices=[[scale,0,0,-scale],[0,scale,scale,0],[-scale,0,0,scale],[0,-scale,-scale,0]];
    if(!matrices.some(matrix=>matrix.every((value,index)=>value===[a,b,c,d][index])))return 'unsupported';
    const points=[[px0,py0],[px0,py1],[px1,py0],[px1,py1]].map(([x,y])=>[e+a*x+c*y,f+b*x+d*y]);
    const expected=[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))];
    if(word.pdf_box.some((value,index)=>Math.abs(value-expected[index])>1e-7))return 'unsupported';
  }
  const match=uniqueQuote(selected.map(word=>word.text),quote);
  if(match.status!=='unique')return match.status;
  const matched=selected.slice(match.start.item,match.end.item+1);
  if(matched.length>1000)return 'unsupported';
  const rectangles=matched.map(word=>[...viewport.convertToViewportPoint(word.pdf_box[0],word.pdf_box[1]),
                                     ...viewport.convertToViewportPoint(word.pdf_box[2],word.pdf_box[3])]);
  if(rectangles.some(rect=>!vector(rect,4)||rect[0]===rect[2]||rect[1]===rect[3]))return 'unsupported';
  for(const rect of rectangles){
    const mark=document.createElement('span');mark.className='pdf-quote-mark';
    mark.style.left=`${Math.min(rect[0],rect[2])}px`;mark.style.top=`${Math.min(rect[1],rect[3])}px`;
    mark.style.width=`${Math.abs(rect[2]-rect[0])}px`;mark.style.height=`${Math.abs(rect[3]-rect[1])}px`;
    container.append(mark);
  }
  return 'unique';
}
