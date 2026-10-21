import re
from argostranslate import translate
def translate_text(text):
    languages=translate.get_installed_languages()
    zh=next((x for x in languages if x.code=='zh'),None)
    en=next((x for x in languages if x.code=='en'),None)
    if not zh or not en:raise RuntimeError('Offline Chinese-to-English language model not installed.')
    engine=zh.get_translation(en)
    parts=re.split(r'(```[\s\S]*?```)',text)
    translated=[]
    for index,part in enumerate(parts):
        if index%2:
            translated.append(part)
            continue
        chunks=[]
        for i in range(0,len(part),1000):chunks.append(engine.translate(part[i:i+1000]))
        translated.append(''.join(chunks))
    return ''.join(translated)

if __name__=="__main__":
 import sys
 sys.stdout.write(translate_text(sys.stdin.read()))
