"""Ingesta local conservadora: formato explícito, hash y transacciones por archivo.

SQLite es el registro operacional; DuckDB se exporta a un archivo nuevo para
revisión, nunca sobre la base que está sirviendo FastAPI. No escribe originales.
"""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from .comparacion_presupuesto import CAMPOS, clave_completa, monto_decimal
except ImportError:
    from comparacion_presupuesto import CAMPOS, clave_completa, monto_decimal

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(texto).casefold()) if c.isalnum())


def leer_xlsx(path):
    with zipfile.ZipFile(path) as z:
        if len(z.infolist())>2000 or sum(x.file_size for x in z.infolist())>50_000_000:
            raise ValueError('XLSX excede límites de extracción')
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            xml=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in n.findall('.//s:t',NS)) for n in xml.findall('s:si',NS)]
        for sheet in sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)):
            rows=[]
            for row in ET.fromstring(z.read(sheet)).findall('s:sheetData/s:row',NS):
                values=[]
                for cell in row.findall('s:c',NS):
                    col=0
                    for char in re.match(r'[A-Z]+',cell.get('r','A1'))[0]:col=col*26+ord(char)-64
                    if col>1000:raise ValueError('XLSX con demasiadas columnas')
                    values.extend([None]*max(0,col-len(values)))
                    value=cell.find('s:v',NS); raw=value.text if value is not None else None
                    if cell.find('s:f',NS) is not None:
                        values[col-1]='FÓRMULA_NO_VERIFICADA'
                    elif cell.get('t')=='s':values[col-1]=shared[int(raw)]
                    elif cell.get('t')=='inlineStr':values[col-1]=''.join(t.text or '' for t in cell.findall('.//s:t',NS))
                    elif cell.get('t','n')=='n' and raw is not None:
                        # OOXML numérico usa punto decimal, independiente del
                        # idioma de Excel. No aplicar formato chileno al raw.
                        values[col-1]=Decimal(raw)
                    else:values[col-1]=raw
                rows.append(values)
            yield sheet,rows


def _monto(valor):
    if isinstance(valor,str):
        # Convención chilena explícita: 1.234,5. Un punto aislado de tres
        # dígitos es separador de miles; el decimal usa coma.
        valor=valor.strip()
        if ',' in valor:valor=valor.replace('.','').replace(',','.')
        elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+',valor):valor=valor.replace('.','')
    m=monto_decimal(valor)
    return str(m) if m is not None else None


def _tablas(rows,ubicacion):
    output=[];issues=[];columns=None;years=[]
    for number,row in enumerate(rows,1):
        normalized=[normalizar(x) for x in row]
        if all(c in normalized for c in CAMPOS):
            if len(normalized)!=len(set(normalized)):
                raise ValueError('Encabezado ambiguo: columnas repetidas')
            columns={v:i for i,v in enumerate(normalized)}
            years=[int(x) for x in normalized if re.fullmatch(r'20\d\d',x)]
            if not years or 'unidad' not in columns or 'moneda' not in columns:
                raise ValueError('Encabezado sin ejercicio, unidad o moneda explícitos')
            continue
        if not columns or not any(str(x or '').strip() for x in row):continue
        def get(key):
            index=columns.get(str(key));return row[index] if index is not None and index<len(row) else None
        try:
            identity=dict(zip(CAMPOS,clave_completa({c:get(c) for c in CAMPOS})))
            unit=str(get('unidad') or '').strip();currency=str(get('moneda') or '').strip()
            if not unit or not currency:raise ValueError('Unidad o moneda ausente')
            parsed=[dict(identity,ano=y,monto=_monto(get(y)),denominacion=str(get('denominacion') or ''),
                         unidad=unit,moneda=currency,ubicacion=ubicacion,fila=number) for y in years]
            output.extend(parsed)
        except (ValueError,TypeError,IndexError) as exc:
            issues.append({'ubicacion':ubicacion,'fila':number,'motivo':str(exc)})
    if columns is None:raise ValueError('No se reconoce una tabla con seis códigos completos')
    return output,issues


def extraer_pdf_texto(texto,pagina=1):
    years=list(dict.fromkeys(re.findall(r'\b20\d\d\b',texto)))
    unidad=re.search(r'Unidad\s*:\s*(miles de pesos|millones de pesos|pesos)\b',texto,re.I)
    moneda=re.search(r'Moneda\s*:\s*([A-Z]{3})\b',texto)
    if len(years)!=2 or not unidad or not moneda:raise ValueError('PDF ambiguo: años, moneda o unidad no explícitos')
    rows=[]
    contexto={}
    etiquetas=unicodedata.normalize('NFKD',texto)
    etiquetas=''.join(c for c in etiquetas if not unicodedata.combining(c))
    for campo in ('partida','capitulo','programa'):
        valores=set(re.findall(rf'\b{campo}\s*:?\s*(\d{{2}})\b',etiquetas,re.I))
        if len(valores)>1:raise ValueError('PDF ambiguo: encabezados de identidad discordantes')
        if valores:contexto[campo]=next(iter(valores))
    pattern=r'^\s*(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{3})\s+(.+?)\s+([\d.,]+|N/D|[-—])\s+([\d.,]+|N/D|[-—])\s*$'
    for number,line in enumerate(texto.splitlines(),1):
        match=re.match(pattern,line,re.I)
        fields=match.groups() if match else None
        if fields is None and len(contexto)==3:
            parcial=re.match(r'^\s*(\d{2})\s+(\d{2})\s+(\d{3})\s+(.+?)\s+([\d.,]+|N/D|[-—])\s+([\d.,]+|N/D|[-—])\s*$',line,re.I)
            if parcial:fields=tuple(contexto[c] for c in ('partida','capitulo','programa'))+parcial.groups()
        if fields:
            identity=dict(zip(CAMPOS,clave_completa(dict(zip(CAMPOS,fields[:6])))))
            for year,amount in zip(years,fields[7:]):
                rows.append(dict(identity,ano=int(year),monto=_monto(amount),denominacion=fields[6],
                                 moneda=moneda[1],unidad=unidad[1].lower(),ubicacion=f'pagina {pagina}',fila=number))
        elif re.match(r'^\s*\d{2}\s+\d{2}\b',line) or re.match(r'^\s*\d{2}\s+.*\s+[\d.,]+\s+[\d.,]+\s*$',line):
            raise ValueError('PDF ambiguo: fila presupuestaria incompleta')
    if not rows:raise ValueError('PDF ambiguo: sin filas con códigos completos')
    return rows


def extraer_archivo(path):
    if path.suffix.lower()=='.xlsx':
        rows=[];issues=[]
        for sheet,table in leer_xlsx(path):
            try:
                r,i=_tablas(table,sheet);rows.extend(r);issues.extend(i)
            except ValueError as exc:issues.append({'ubicacion':sheet,'motivo':str(exc)})
        return rows,issues
    if path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:return _tablas(list(csv.reader(f)),path.name)
    if path.suffix.lower()=='.pdf':
        from pypdf import PdfReader
        reader=PdfReader(path)
        if len(reader.pages)>1000:raise ValueError('PDF excede límite de páginas')
        rows=[]
        for number,page in enumerate(reader.pages,1):
            text=page.extract_text() or ''
            # Una página no tabular se admite; una página con datos sin
            # identidad completa rechaza el documento financiero completo.
            presupuestaria = re.search(r'^\s*\d{2}\s+.*\s+[\d.,]+\s+[\d.,]+\s*$',text,re.M)
            if presupuestaria or re.search(r'^\s*\d{2}\s+\d{2}\b',text,re.M):
                rows.extend(extraer_pdf_texto(text,number))
        if not rows:raise ValueError('PDF ambiguo: sin tabla verificable; requiere revisión local')
        return rows,[]
    raise ValueError('Formato no soportado: usar XLSX, CSV o PDF estructurado')


def _schema(con):
    con.executescript('''CREATE TABLE IF NOT EXISTS archivos(
        sha256 TEXT PRIMARY KEY, ruta TEXT NOT NULL, estado TEXT NOT NULL,
        fecha TEXT NOT NULL, incidencias TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS presupuesto(
        documento_id TEXT NOT NULL REFERENCES archivos(sha256), ano INTEGER NOT NULL,
        partida TEXT,capitulo TEXT,programa TEXT,subtitulo TEXT,item TEXT,asignacion TEXT,
        monto TEXT,denominacion TEXT,unidad TEXT,moneda TEXT,ubicacion TEXT,fila INTEGER,
        UNIQUE(documento_id,ano,ubicacion,fila));''')


def ingerir_lote(archivos,sqlite_path,rechazados_path):
    db=Path(sqlite_path);log=Path(rechazados_path)
    db.parent.mkdir(parents=True,exist_ok=True);log.parent.mkdir(parents=True,exist_ok=True)
    resultados=[]
    with sqlite3.connect(db,timeout=10) as con:
        con.execute('PRAGMA foreign_keys=ON');_schema(con)
        for input_path in archivos:
            path=Path(input_path);digest=None;issues=[];rows=[]
            try:
                with path.open('rb') as f:
                    digest=hashlib.file_digest(f,'sha256').hexdigest()
                existing=con.execute('SELECT estado FROM archivos WHERE sha256=?',(digest,)).fetchone()
                if existing:
                    resultados.append({'archivo':str(path),'sha256':digest,'estado':'ya_ingestado','estado_original':existing[0],'registros':0});continue
                rows,issues=extraer_archivo(path)
                with path.open('rb') as f:
                    if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise ValueError('Fuente cambió durante extracción')
                if not rows:issues.append({'motivo':'Sin registros presupuestarios verificables'})
            except Exception as exc:
                rows=[];issues.append({'motivo':f'{type(exc).__name__}: {exc}'})
            estado='rechazado' if not rows else ('parcial' if issues else 'ingestado')
            if digest:
                with con:
                    con.execute('BEGIN IMMEDIATE')
                    # Dos procesos pueden extraer el mismo documento antes de
                    # entrar a la transacción. Revalidar bajo el lock SQLite.
                    existing=con.execute('SELECT estado FROM archivos WHERE sha256=?',(digest,)).fetchone()
                    if existing:
                        resultados.append({'archivo':str(path),'sha256':digest,'estado':'ya_ingestado','estado_original':existing[0],'registros':0})
                        continue
                    con.execute('INSERT INTO archivos VALUES(?,?,?,?,?)',(digest,str(path),estado,datetime.now(timezone.utc).isoformat(),json.dumps(issues,ensure_ascii=False)))
                    for row in rows:
                        vals=[digest,row['ano']]+[row[c] for c in CAMPOS]+[row[k] for k in ('monto','denominacion','unidad','moneda','ubicacion','fila')]
                        con.execute('INSERT INTO presupuesto VALUES('+','.join('?' for _ in vals)+')',vals)
            if issues:
                with log.open('a',encoding='utf-8') as f:
                    for issue in issues:f.write(json.dumps(dict(issue,archivo=str(path),sha256=digest,estado=estado),ensure_ascii=False)+'\n')
            resultados.append({'archivo':str(path),'sha256':digest,'estado':estado,'registros':len(rows)})
    return resultados


def comparar_sqlite(sqlite_path, *, ipc=None, ano_base=2025, ano_objetivo=2026):
    try:
        from .comparacion_presupuesto import comparar_presupuestos
    except ImportError:
        from comparacion_presupuesto import comparar_presupuestos
    with sqlite3.connect(f'file:{Path(sqlite_path).resolve().as_posix()}?mode=ro',uri=True) as con:
        con.row_factory=sqlite3.Row
        filas=[dict(r) for r in con.execute('SELECT * FROM presupuesto WHERE ano IN (?,?)',(ano_base,ano_objetivo))]
    return comparar_presupuestos([r for r in filas if r['ano']==ano_base],
                                [r for r in filas if r['ano']==ano_objetivo],
                                ano_base=ano_base,ano_objetivo=ano_objetivo,ipc=ipc)


def exportar_duckdb(sqlite_path,destino):
    import duckdb
    destino=Path(destino)
    if destino.exists():raise FileExistsError('Exportar a una base nueva; no sobrescribir original')
    destino.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(sqlite_path) as sqlite,duckdb.connect(str(destino)) as duck:
        duck.execute('BEGIN TRANSACTION')
        duck.execute('CREATE TABLE ingesta_archivos(sha256 VARCHAR PRIMARY KEY,ruta VARCHAR,estado VARCHAR,fecha VARCHAR,incidencias VARCHAR)')
        duck.execute('CREATE TABLE presupuesto_normalizado(documento_id VARCHAR,ano INTEGER,partida VARCHAR,capitulo VARCHAR,programa VARCHAR,subtitulo VARCHAR,item VARCHAR,asignacion VARCHAR,monto DECIMAL(30,6),denominacion VARCHAR,unidad VARCHAR,moneda VARCHAR,ubicacion VARCHAR,fila INTEGER)')
        for row in sqlite.execute('SELECT * FROM archivos'):duck.execute('INSERT INTO ingesta_archivos VALUES(?,?,?,?,?)',row)
        for row in sqlite.execute('SELECT * FROM presupuesto'):duck.execute('INSERT INTO presupuesto_normalizado VALUES('+','.join('?' for _ in row)+')',row)
        duck.execute('COMMIT')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivos',nargs='+',type=Path)
    parser.add_argument('--sqlite',required=True,type=Path)
    parser.add_argument('--rechazados',type=Path,default=Path('inbox/rechazados.ndjson'))
    parser.add_argument('--duckdb-nuevo',type=Path)
    args=parser.parse_args()
    print(json.dumps(ingerir_lote(args.archivos,args.sqlite,args.rechazados),ensure_ascii=False,indent=2))
    if args.duckdb_nuevo:exportar_duckdb(args.sqlite,args.duckdb_nuevo)
