"""Generate a wholly synthetic text PDF, with no external assets or corporate data."""
from io import BytesIO

def text_pdf(text='Pump-X maximum operating temperature is 75 C'):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer=PdfWriter(); page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject(); text=text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream.set_data(f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode())
    page[NameObject('/Contents')]=writer._add_object(stream)
    out=BytesIO(); writer.write(out); return out.getvalue()

if __name__=='__main__':
    from pathlib import Path
    target=Path(__file__).resolve().parents[1]/'datasets/synthetic/pump-x-revision-2.pdf'
    target.write_bytes(text_pdf())
    print('Synthetic PDF generated:',target.name)
