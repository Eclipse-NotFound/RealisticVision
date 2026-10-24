from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parents[2]/'build/frame-attribution-output'
main=OUT/'loader-order/scripts/MainFE.as';menu=OUT/'native-source/scripts/fe/MainMenu.as'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((OUT/'loader-order/fingerprints.json').read_text());assert sha(main)==pins['source']
checked=json.loads((OUT/'native-source/checked.json').read_text());assert sha(menu)==checked['mainMenuSource'] and pins['host']==checked['host']
s=main.read_text(encoding='utf-8-sig');assert s.index('this.mainMenu = new MainMenu(this);')<s.index('this.loadModsFromManifest();')
s=menu.read_text(encoding='utf-8-sig');assert 'addEventListener(Event.ENTER_FRAME,this.mainStep)' in s
result={'host':pins['host'],'mainFE':sha(main),'mainMenu':sha(menu),'verified':['native mainMenu created before manifest loading','native stage mainStep listener default priority zero'],'scope':'Specific host only; serial and world-step runtime checks are in native-timing-02'}
(OUT/'order-reviewed.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print('Order and exact source verified')
