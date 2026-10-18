// CSS coordinates remain the citation coordinate space at every display density.
export function canvasGeometry(width,height,deviceRatio=1){
 const cssWidth=Math.ceil(width),cssHeight=Math.ceil(height),budget=16000000,maximumSide=16384;
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0||cssWidth>maximumSide||cssHeight>maximumSide||cssWidth*cssHeight>budget)
  throw Error('Page exceeds the viewer pixel budget.');
 const ratio=Number.isFinite(deviceRatio)?Math.max(1,Math.min(3,deviceRatio)):1;
 const scale=Math.min(ratio,Math.sqrt(budget/(cssWidth*cssHeight)),maximumSide/cssWidth,maximumSide/cssHeight);
 const pixelWidth=Math.max(1,Math.floor(cssWidth*scale)),pixelHeight=Math.max(1,Math.floor(cssHeight*scale));
 return {width,height,pixelWidth,pixelHeight,transform:[pixelWidth/width,0,0,pixelHeight/height,0,0]};
}
