#!/usr/bin/env python3
import sys, sqlite3, pathlib, json, subprocess, os
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QTableWidget,QTableWidgetItem,QPushButton,QComboBox,QPlainTextEdit,QLabel,QSplitter,QMessageBox,QLineEdit,QScrollArea,QDateEdit,QDialog,QFormLayout,QProgressBar,QFileDialog
from PySide6.QtCore import Qt, QThread, Signal, QDate, QDate
from PySide6.QtGui import QShortcut, QKeySequence

STYLE = '''
QWidget { background: #0b1020; color: #dbeafe; font-family: 'DejaVu Sans'; font-size: 12px; }
QLabel#heading { color: #54e9ff; font-size: 21px; font-weight: 800; padding-top: 4px; }
QLabel#subtitle { color: #bd8cff; font-size: 11px; letter-spacing: 1px; }
QLabel#status { color: #94a3b8; }
QTableWidget, QPlainTextEdit { background: #101a31; color: #dceaff; border: 1px solid #2b3959; border-radius: 8px; padding: 6px; selection-background-color: #5e35a8; selection-color: white; font-family: 'DejaVu Sans Mono'; font-size: 12px; }
QHeaderView::section { background: #202b49; color: #80f7ec; font-weight: bold; border: 0; padding: 9px; }
QTableWidget::item { padding: 4px; }
QPushButton { background: #203252; border: 1px solid #48618f; border-radius: 7px; padding: 10px 15px; font-weight: 700; color: #c8f9ff; }
QPushButton:hover { background: #354b78; border-color: #56eaff; }
QPushButton:disabled { color: #66728e; background: #15213a; }
QLineEdit { background: #172747; color: #dbeafe; border: 1px solid #53639b; border-radius: 7px; padding: 11px; font-size: 13px; }
QScrollArea { background: #0e162b; border: 1px solid #273958; border-radius: 7px; }
QPushButton[segment="true"] { background: #19253e; border-color: #374461; color: #b8c8eb; padding: 9px; }
QPushButton[active="true"] { background: #4b2777; border: 1px solid #52e4fa; color: #ffffff; }
QComboBox { background: #172747; color: #e6e8ff; border: 1px solid #53639b; border-radius: 7px; padding: 9px; }
QSplitter::handle { background: #273958; }
QScrollBar:vertical { background: #111c32; width: 11px; }
QScrollBar::handle:vertical { background: #405077; border-radius: 5px; }
'''

BASE=pathlib.Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else pathlib.Path(__file__).resolve().parent
DB=BASE/'openrouter-logs-EN-WORKING.sqlite'
WORKER=BASE/'openrouter_translate_worker.py'
PYTHON=sys.executable
class TranslationThread(QThread):
 done=Signal(str,str)
 def __init__(self,text):super().__init__();self.input_text=text
 def run(self):
  try:
   script=BASE/'openrouter_translate_worker.py'
   python=str(pathlib.Path.home()/'.local/share/openrouter-translator-venv/bin/python')
   result=subprocess.run([python,str(script)],input=self.input_text,capture_output=True,text=True,timeout=900)
   if result.returncode:self.done.emit('',result.stderr[-450:] or 'Offline translation failed')
   else:self.done.emit(result.stdout,'')
  except Exception as e:self.done.emit('',str(e))
class RecoveryWorker(QThread):
 progress=Signal(str)
 done=Signal(str,str)
 def __init__(self,database,start,end,key):
  super().__init__();self.database=database;self.start=start;self.end=end;self.key=key
 def run(self):
  try:
   from openrouter_recovery import recover
   output=recover(str(self.database),self.start,self.end,self.key,self.progress.emit)
   self.done.emit(output,'')
  except Exception as e:self.done.emit('',str(e))
  finally:self.key=None

class RecoverDialog(QDialog):
 def __init__(self,parent):
  super().__init__(parent);self.parent_viewer=parent;self.setWindowTitle('◈ ARCHIVE RECOVERY  /  OPENROUTER');self.resize(620,430)
  layout=QVBoxLayout(self)
  layout.addWidget(QLabel('RECOVER HISTORICAL REQUESTS  //  MANAGEMENT KEY REQUIRED'))
  self.start=QDateEdit();self.start.setCalendarPopup(True);self.start.setDate(QDate.currentDate().addDays(-7))
  self.end=QDateEdit();self.end.setCalendarPopup(True);self.end.setDate(QDate.currentDate())
  self.key=QLineEdit();self.key.setEchoMode(QLineEdit.Password);self.key.setPlaceholderText('Paste management key (not saved)')
  form=QFormLayout();form.addRow('From (UTC)',self.start);form.addRow('Through (UTC)',self.end);form.addRow('Management key',self.key);layout.addLayout(form)
  layout.addWidget(QLabel('Uses OpenRouter analytics to enumerate generation IDs, then retrieves metadata and stored content.'))
  self.go=QPushButton('◈ RECOVER INTO LOCAL ARCHIVE');self.go.clicked.connect(self.begin);layout.addWidget(self.go)
  self.status=QPlainTextEdit();self.status.setReadOnly(True);layout.addWidget(self.status)
 def begin(self):
  if not self.key.text().strip():QMessageBox.warning(self,'Missing key','Please provide an OpenRouter management key.');return
  if self.start.date()>self.end.date():QMessageBox.warning(self,'Invalid dates','Start is after end.');return
  self.go.setEnabled(False)
  self.worker=RecoveryWorker(DB,self.start.date().toString('yyyy-MM-dd'),self.end.date().toString('yyyy-MM-dd'),self.key.text().strip())
  self.key.clear()
  self.worker.progress.connect(self.status.appendPlainText)
  self.worker.done.connect(self.completed)
  self.worker.start()
 def completed(self,message,error):
  self.go.setEnabled(True)
  self.status.appendPlainText(error if error else message)
  if error:QMessageBox.warning(self,'Recovery issue',error)
  else:self.parent_viewer.load()

class Window(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('JL // OPENROUTER ARCHIVE :: TRANSLATION CONSOLE');self.resize(1530,900)
  self.setStyleSheet(STYLE)
  from PySide6.QtGui import QIcon
  icon=BASE/'archive_icon.ico'
  if icon.exists():self.setWindowIcon(QIcon(str(icon)))
  self.db=sqlite3.connect(str(DB));self.db.execute('CREATE TABLE IF NOT EXISTS english_translations (generation_id TEXT, field_name TEXT, translated_text TEXT, translated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(generation_id,field_name))');self.db.commit()
  v=QVBoxLayout(self);v.setContentsMargins(16,16,16,16);v.setSpacing(11)
  heading=QLabel('◈  OPENROUTER  /  ARCHIVE EXPLORER');heading.setObjectName('heading');v.addWidget(heading)
  subtitle=QLabel('RECOVERED GENERATIONS   •   LOCAL DATABASE   •   BILINGUAL INSPECTION');subtitle.setObjectName('subtitle');v.addWidget(subtitle)
  self.message=QLabel('Select a generation. Original records are preserved.');self.message.setObjectName('status');v.addWidget(self.message)
  top=QHBoxLayout();top.setSpacing(10);v.addLayout(top)
  self.field=QComboBox();self.field.addItems(['prompt_text','completion_text','reasoning_text']);top.addWidget(self.field)
  self.translate=QPushButton('◈ TRANSLATE → ENGLISH');top.addWidget(self.translate)
  self.refresh=QPushButton('↻ REFRESH');top.addWidget(self.refresh)
  self.metrics_button=QPushButton('◈ METRICS EXPLORER');self.metrics_button.setToolTip('Browse every SQLite analytics table and choose your own visible metrics');self.metrics_button.clicked.connect(self.show_metrics);top.addWidget(self.metrics_button)
  self.import_button=QPushButton('◈ IMPORT DATABASE');self.import_button.clicked.connect(self.import_file);top.addWidget(self.import_button)
  self.recover_button=QPushButton('◈ IMPORT / RECOVER');self.recover_button.clicked.connect(self.show_recovery);top.addWidget(self.recover_button)
  self.search=QLineEdit();self.search.setPlaceholderText('⌕ Search models, IDs, prompts, replies…');v.addWidget(self.search)
  self.blip_scroller=QScrollArea();self.blip_scroller.setWidgetResizable(True);self.blip_scroller.setFixedHeight(68);self.blip_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded);self.blip_scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
  self.blip_host=QWidget();self.blip_row=QHBoxLayout(self.blip_host);self.blip_row.setContentsMargins(5,4,5,4);self.blip_row.setSpacing(7);self.blip_scroller.setWidget(self.blip_host);v.addWidget(self.blip_scroller)
  self.parts=[];self.selected_part=0
  self.previous=QPushButton("◀");self.previous.setToolTip("Previous section (Left arrow)");self.previous.clicked.connect(lambda:self.move_part(-1));top.addWidget(self.previous)
  self.next=QPushButton("▶");self.next.setToolTip("Next section (Right arrow)");self.next.clicked.connect(lambda:self.move_part(1));top.addWidget(self.next);top.addStretch(1)
  self.left_key=QShortcut(QKeySequence(Qt.Key_Left),self);self.left_key.activated.connect(lambda:self.move_part(-1))
  self.right_key=QShortcut(QKeySequence(Qt.Key_Right),self);self.right_key.activated.connect(lambda:self.move_part(1))
  s=QSplitter(Qt.Vertical);v.addWidget(s)
  self.table=QTableWidget();self.table.setColumnCount(6);self.table.setHorizontalHeaderLabels(['Generation ID','UTC','Model','Prompt tokens','Reply tokens','EN translations']);self.table.setSelectionBehavior(QTableWidget.SelectRows);self.table.setEditTriggers(QTableWidget.NoEditTriggers);s.addWidget(self.table)
  texts=QSplitter(Qt.Horizontal);s.addWidget(texts)
  left=QWidget();lv=QVBoxLayout(left);lv.addWidget(QLabel('SOURCE  //  ORIGINAL • UNALTERED'));self.original=QPlainTextEdit();self.original.setReadOnly(True);lv.addWidget(self.original);texts.addWidget(left)
  right=QWidget();rv=QVBoxLayout(right);rv.addWidget(QLabel('TARGET  //  ENGLISH • SAVED TO WORKING COPY'));self.english=QPlainTextEdit();self.english.setReadOnly(True);rv.addWidget(self.english);texts.addWidget(right)
  s.setSizes([340,500]);self.current=None
  self.table.itemSelectionChanged.connect(self.show_record);self.field.currentIndexChanged.connect(self.show_record);self.translate.clicked.connect(self.run_translate);self.refresh.clicked.connect(self.load);self.search.textChanged.connect(self.filter_rows)
  self.load()
 def show_metrics(self):
  from archive_metrics_explorer import MetricsExplorer
  self.metrics_window=MetricsExplorer(DB,self)
  self.metrics_window.setStyleSheet(STYLE)
  self.metrics_window.show()
 def import_file(self):
  filename,_=QFileDialog.getOpenFileName(self,'Choose a SQLite archive',str(pathlib.Path.home()),'SQLite databases (*.sqlite *.sqlite3 *.db);;All files (*)')
  if not filename:return
  from openrouter_db_import import import_database
  try:
   result=import_database(DB,filename)
   self.load()
   self.message.setText(result)
   QMessageBox.information(self,'Database import completed',result)
  except Exception as error:
   QMessageBox.warning(self,'Database import failed',str(error))
 def show_recovery(self):
  dlg=RecoverDialog(self);dlg.exec()
 def show_recovery(self):
  dlg=RecoverDialog(self);dlg.exec()
 def load(self):
  rows=self.db.execute('SELECT g.id,g.created_at_utc,g.model,g.tokens_prompt,g.tokens_completion,(SELECT count(*) FROM english_translations t WHERE t.generation_id=g.id) FROM generations g ORDER BY g.created_at_utc DESC').fetchall()
  self.table.setRowCount(len(rows))
  for i,row in enumerate(rows):
   for j,value in enumerate(row):self.table.setItem(i,j,QTableWidgetItem(str(value or '')))
  self.table.resizeColumnsToContents();self.filter_rows(self.search.text());self.message.setText(f'{len(rows):,} generations. Click any row to inspect and translate.')
 def filter_rows(self,text):
  needle=text.strip().lower()
  if not needle:
   for i in range(self.table.rowCount()):self.table.setRowHidden(i,False)
   return
  # Search full archive texts in SQLite, rather than loading huge prompts into the UI.
  ids=set()
  for (gid,) in self.db.execute("SELECT id FROM generations WHERE lower(id) LIKE ? OR lower(model) LIKE ? OR lower(coalesce(prompt_text,'')) LIKE ? OR lower(coalesce(completion_text,'')) LIKE ? LIMIT 3000",(('%'+needle+'%',)*4)):
   ids.add(gid)
  for i in range(self.table.rowCount()):
   self.table.setRowHidden(i,self.table.item(i,0).text() not in ids)
 def show_record(self):
  i=self.table.currentRow()
  if i<0:return
  gid=self.table.item(i,0).text();self.current=gid
  row=self.db.execute("SELECT prompt_messages_json,completion_text,reasoning_text,raw_content_json,prompt_text FROM generations WHERE id=?",(gid,)).fetchone()
  if not row:return
  import json
  try:messages=json.loads(row[0] or '[]')
  except (ValueError,TypeError):messages=[]
  segments=[]
  for n,m in enumerate(messages):
   if not isinstance(m,dict):continue
   role=str(m.get('role') or 'message').upper()
   val=m.get('content')
   content=val if isinstance(val,str) else json.dumps(val,ensure_ascii=False,indent=2)
   if not content:continue
   segments.append((role,content,None))
  if not segments and row[4]:segments.append(('PROMPT',row[4],'prompt_text'))
  if row[2]:segments.append(('REASONING',row[2],'reasoning_text'))
  if row[1]:segments.append(('REPLY',row[1],'completion_text'))
  # Surface output tool/function calls even when they aren't in completion_text.
  try:
   raw=json.loads(row[3] or '{}');out=raw.get('output') or {}
   if isinstance(out,dict):
    for name in ('tool_calls','function_call','tool_use'):
     if out.get(name):segments.append(('TOOL CALLS',json.dumps(out[name],ensure_ascii=False,indent=2),None))
  except (ValueError,TypeError):pass
  full='\n\n'.join(f'════ {role} [{n+1}] ════\n{content}' for n,(role,content,_) in enumerate(segments))
  # Every column in the generations row remains accessible, not just the text fields.
  self.db.row_factory=sqlite3.Row
  record=self.db.execute('SELECT * FROM generations WHERE id=?',(gid,)).fetchone()
  values={key:record[key] for key in record.keys()} if record else {}
  metadata={k:v for k,v in values.items() if k not in ('prompt_messages_json','prompt_text','completion_text','reasoning_text','raw_metadata_json','raw_content_json') and v is not None}
  metadata_text=json.dumps(metadata,ensure_ascii=False,indent=2,default=str)
  if metadata:segments.append(('METADATA',metadata_text,'metadata_json'))
  for col,title in [('raw_metadata_json','RAW METADATA'),('raw_content_json','RAW CONTENT'),('prompt_messages_json','RAW MESSAGES')]:
   value=values.get(col)
   if value:
    try:formatted=json.dumps(json.loads(value),ensure_ascii=False,indent=2)
    except (TypeError,ValueError):formatted=str(value)
    segments.append((title,formatted,col))
  full='\n\n'.join(f'════ {role} [{n+1}] ════\n{content}' for n,(role,content,_) in enumerate(segments))
  self.parts=[('FULL',full,'full_transcript')]+segments
  while self.blip_row.count():
   it=self.blip_row.takeAt(0)
   if it.widget():it.widget().deleteLater()
  for n,(role,content,field) in enumerate(self.parts):
   btn=QPushButton(f'{n+1:02} · {role}')
   btn.setProperty('segment',True)
   btn.clicked.connect(lambda _=False,index=n:self.select_part(index))
   self.blip_row.addWidget(btn)
  self.blip_row.addStretch(1)
  self.select_part(0)
 def select_part(self,index):
  if not self.parts:return
  self.selected_part=index
  role,content,field=self.parts[index]
  self.original.setPlainText(content)
  self.active_field=field
  key=field or ('message_'+str(index))
  existing=self.db.execute('SELECT translated_text FROM english_translations WHERE generation_id=? AND field_name=?',(self.current,key)).fetchone()
  self.english.setPlainText(existing[0] if existing else '')
  self.message.setText(f'{index+1}/{len(self.parts)} • {role} • {len(content):,} characters')
  for n in range(self.blip_row.count()):
   widget=self.blip_row.itemAt(n).widget()
   if isinstance(widget,QPushButton):widget.setProperty('active',n==index);widget.style().unpolish(widget);widget.style().polish(widget)
 def move_part(self,delta):
  if self.parts:self.select_part(max(0,min(len(self.parts)-1,self.selected_part+delta)))
 def run_translate(self):
  text=self.original.toPlainText()
  if not text.strip():self.message.setText('No text in this field');return
  self.target=(self.current,self.active_field or ('message_'+str(self.selected_part)));self.translate.setEnabled(False);self.message.setText('Translating locally...')
  self.thread=TranslationThread(text);self.thread.done.connect(self.finished);self.thread.start()
 def finished(self,result,error):
  self.translate.setEnabled(True)
  if error:
   self.message.setText('Translation unavailable. See details.')
   QMessageBox.warning(self,'Translation unavailable',error);return
  self.db.execute('INSERT OR REPLACE INTO english_translations(generation_id,field_name,translated_text) VALUES(?,?,?)',(*self.target,result));self.db.commit()
  self.message.setText('English translation saved inside working SQLite copy.')
  self.select_part(self.selected_part)
if __name__=='__main__':
 app=QApplication(sys.argv);w=Window();w.show();sys.exit(app.exec())
