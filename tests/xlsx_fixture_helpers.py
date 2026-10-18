"""Small standards-shaped OOXML fixture; never executes formulas."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED

NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'


def workbook(overrides=None,extra=None):
    parts={
        '[Content_Types].xml':b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>',
        '_rels/.rels':f'<Relationships xmlns="{P}"><Relationship Id="root" Type="{R}/officeDocument" Target="xl/workbook.xml"/></Relationships>'.encode(),
        'xl/workbook.xml':f'<workbook xmlns="{NS}" xmlns:r="{R}"><sheets><sheet name="Visible" sheetId="1" r:id="s1"/><sheet name="Hidden" sheetId="2" state="hidden" r:id="s2"/></sheets></workbook>'.encode(),
        'xl/_rels/workbook.xml.rels':f'<Relationships xmlns="{P}"><Relationship Id="s1" Type="{R}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="s2" Type="{R}/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="strings" Type="{R}/sharedStrings" Target="sharedStrings.xml"/></Relationships>'.encode(),
        'xl/sharedStrings.xml':f'<sst xmlns="{NS}" count="1" uniqueCount="1"><si><r><t xml:space="preserve"> leading </t></r><r><t>text</t></r></si></sst>'.encode(),
        'xl/worksheets/sheet1.xml':f'<worksheet xmlns="{NS}"><dimension ref="A1"/><sheetData><row r="1"><c r="A1"><v>001.2300</v></c><c r="B1"><f>SUM(A1:A2)</f><v>999.1</v></c><c r="C1" t="s"><v>0</v></c></row><row r="9"><c r="Z9" t="inlineStr"><is><t>late cell</t></is></c></row></sheetData><mergeCells><mergeCell ref="D1:E1"/></mergeCells></worksheet>'.encode(),
        'xl/worksheets/sheet2.xml':f'<worksheet xmlns="{NS}"><sheetData><row r="1" hidden="1"><c r="A1" t="b"><v>0</v></c><c r="B1" t="e"><v>#DIV/0!</v></c><c r="C1"/><c r="D1" t="inlineStr"><is><t/></is></c></row></sheetData></worksheet>'.encode(),
    }
    parts.update(overrides or {});parts.update(extra or {})
    output=BytesIO()
    with ZipFile(output,'w',compression=ZIP_DEFLATED) as archive:
        for name,value in parts.items():archive.writestr(name,value)
    return output.getvalue()
