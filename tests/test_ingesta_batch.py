import csv
import json
import sqlite3
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ingesta_batch import ingerir_lote, exportar_duckdb, extraer_pdf_texto

CABECERA=['Partida','Capítulo','Programa','Subtítulo','Ítem','Asignación',
          'Denominación','2025','2026','Unidad','Moneda']


def fuente(path, filas):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(CABECERA);w.writerows(filas)
    return path


def fila():return ['05','01','02','24','01','001','Programa ejemplo',100,110,'pesos','CLP']


def test_idempotencia_por_contenido_incluso_renombrado(tmp_path):
    p=fuente(tmp_path/'a.csv',[fila()]); db=tmp_path/'traza.sqlite'; log=tmp_path/'rechazados.ndjson'
    primero=ingerir_lote([p],db,log)
    copia=tmp_path/'copia.csv';copia.write_bytes(p.read_bytes())
    segundo=ingerir_lote([p,copia],db,log)
    with sqlite3.connect(db) as c:
        assert c.execute('SELECT count(*) FROM presupuesto').fetchone()[0]==2
        assert c.execute('SELECT count(*) FROM archivos').fetchone()[0]==1
    assert primero[0]['estado']=='ingestado'
    assert all(x['estado']=='ya_ingestado' for x in segundo)


def test_fila_corrupta_no_aborta_archivo_ni_lote(tmp_path):
    mala=fila();mala[7]='inventado'
    p=fuente(tmp_path/'a.csv',[fila(),mala]); corrupto=tmp_path/'b.xlsx';corrupto.write_bytes(b'no zip')
    db=tmp_path/'traza.sqlite';log=tmp_path/'rechazados.ndjson'
    r=ingerir_lote([corrupto,p],db,log)
    assert [x['estado'] for x in r]==['rechazado','parcial']
    with sqlite3.connect(db) as c:assert c.execute('SELECT count(*) FROM presupuesto').fetchone()[0]==2
    motivos=[json.loads(x)['motivo'] for x in log.read_text().splitlines()]
    assert len(motivos)>=2


def test_null_no_se_convierte_en_cero(tmp_path):
    f=fila();f[8]='N/D';p=fuente(tmp_path/'a.csv',[f]);db=tmp_path/'t.sqlite'
    ingerir_lote([p],db,tmp_path/'r.ndjson')
    with sqlite3.connect(db) as c:assert c.execute('SELECT monto FROM presupuesto WHERE ano=2026').fetchone()[0] is None


def test_pdf_ambiguo_se_rechaza():
    with pytest.raises(ValueError,match='ambiguo'):
        extraer_pdf_texto('PARTIDA 05\nCapítulo 01\nPrograma 02\n24 Transferencias 100 110')


def test_pdf_completo_y_unidad_explicita():
    texto='Presupuesto 2025 2026\nMoneda: CLP; Unidad: miles de pesos\n05 01 02 24 01 001 Programa ejemplo 100 110'
    rows=extraer_pdf_texto(texto)
    assert len(rows)==2 and rows[1]['monto']=='110'
    assert rows[0]['asignacion']=='001' and rows[0]['unidad']=='miles de pesos'


def test_exportacion_duckdb_conserva_traza_y_null(tmp_path):
    f=fila();f[8]='';p=fuente(tmp_path/'a.csv',[f]);db=tmp_path/'t.sqlite';dest=tmp_path/'nuevo.duckdb'
    ingerir_lote([p],db,tmp_path/'r.ndjson');exportar_duckdb(db,dest)
    with duckdb.connect(str(dest),read_only=True) as c:
        assert c.execute('SELECT count(*) FROM ingesta_archivos').fetchone()[0]==1
        assert c.execute('SELECT monto FROM presupuesto_normalizado WHERE ano=2026').fetchone()[0] is None
    with pytest.raises(FileExistsError):exportar_duckdb(db,dest)


def test_xlsx_real_sin_motor_adicional(tmp_path):
    import zipfile
    from xml.sax.saxutils import escape
    rows=[CABECERA,fila()]; xml=[]
    for i,row in enumerate(rows,1):
        cells=''.join(f'<c r="{chr(65+j)}{i}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>' for j,v in enumerate(row))
        xml.append(f'<row r="{i}">{cells}</row>')
    p=tmp_path/'a.xlsx'
    with zipfile.ZipFile(p,'w') as z:z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(xml)+'</sheetData></worksheet>')
    r=ingerir_lote([p],tmp_path/'t.sqlite',tmp_path/'r.ndjson')
    assert r[0]['registros']==2


def test_originales_no_cambian(tmp_path):
    p=fuente(tmp_path/'a.csv',[fila()]);original=p.read_bytes()
    ingerir_lote([p],tmp_path/'t.sqlite',tmp_path/'r.ndjson')
    assert p.read_bytes()==original


def test_idempotencia_concurrente(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    p=fuente(tmp_path/'a.csv',[fila()]);db=tmp_path/'t.sqlite';log=tmp_path/'r.ndjson'
    with ThreadPoolExecutor(max_workers=3) as pool:
        resultados=list(pool.map(lambda _:ingerir_lote([p],db,log),range(3)))
    assert sum(r[0]['estado']=='ingestado' for r in resultados)==1
    with sqlite3.connect(db) as c:assert c.execute('SELECT count(*) FROM presupuesto').fetchone()[0]==2


def test_comparacion_persistida_usa_codigo_completo(tmp_path):
    from ingesta_batch import comparar_sqlite
    p=fuente(tmp_path/'a.csv',[fila()]);db=tmp_path/'t.sqlite'
    ingerir_lote([p],db,tmp_path/'r.ndjson')
    r=comparar_sqlite(db)
    assert len(r)==1 and r[0]['variacion_nominal_pct']==10
    assert r[0]['variacion_real_pct'] is None


def test_pdf_fisico_estructurado_y_ambiguo(tmp_path):
    # PDF mínimo con texto real: ninguna dependencia adicional para fixtures.
    def pdf(path,text):
        stream=('BT /F1 12 Tf 40 700 Td '+ ' '.join('('+line+') Tj 0 -20 Td' for line in text.splitlines())+' ET').encode()
        bodies=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
        out=b'%PDF-1.4\n';offsets=[]
        for i,b in enumerate(bodies,1):offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+b+b'\nendobj\n'
        xref=len(out);out+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets)
        out+=f'trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode();path.write_bytes(out)
    bueno=tmp_path/'bueno.pdf';malo=tmp_path/'ambiguo.pdf'
    pdf(bueno,'Presupuesto 2025 2026\nMoneda: CLP; Unidad: pesos\n05 01 02 24 01 001 Programa ejemplo 100 110')
    pdf(malo,'Presupuesto 2025 2026\n24 Transferencias 100 110')
    r=ingerir_lote([bueno,malo],tmp_path/'t.sqlite',tmp_path/'r.ndjson')
    assert r[0]['registros']==2 and r[1]['estado']=='rechazado'


def test_decimal_numerico_excel_no_se_interpreta_como_miles(tmp_path):
    import zipfile
    from xml.sax.saxutils import escape
    header=''.join(f'<c r="{chr(65+j)}1" t="inlineStr"><is><t>{escape(v)}</t></is></c>' for j,v in enumerate(CABECERA))
    data=fila();data[7]='1.234'
    body=''.join(f'<c r="{chr(65+j)}2"><v>{v}</v></c>' if j==7 else f'<c r="{chr(65+j)}2" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>' for j,v in enumerate(data))
    p=tmp_path/'a.xlsx'
    with zipfile.ZipFile(p,'w') as z:z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>'+header+'</row><row>'+body+'</row></sheetData></worksheet>')
    db=tmp_path/'t.sqlite';ingerir_lote([p],db,tmp_path/'r.ndjson')
    with sqlite3.connect(db) as c:assert c.execute('SELECT monto FROM presupuesto WHERE ano=2025').fetchone()[0]=='1.234'
