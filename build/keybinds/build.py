"""Build shortcuts on the installed v0.30.5 lineage, excluding other pending features."""
from pathlib import Path
import hashlib, json, re, shutil, sys

MOD = Path(__file__).resolve().parents[2]
BASE = MOD / 'build/wall-surface-output/baseline/src'
OUT = MOD / 'build/keybind-output'
PIN = '6979263b178b4deedf563a88c560614bd867d4fad89d806484b5a5b851c0d446'


def integrate(text, stamp_version=True):
    def change(old, new):
        nonlocal text
        assert text.count(old) == 1, f'Expected unique anchor: {old[:80]}'
        text = text.replace(old, new)
    change('      private var cfgEnabled:Boolean = true;',
           '      private var cfgEnabled:Boolean = true;\n      private var keybinds:RVKeybinds = new RVKeybinds();')
    change('      private function onKeyDown(e:KeyboardEvent):void\n      {\n         if(e.keyCode == Keyboard.F10)',
           '      private function onKeyDown(e:KeyboardEvent):void\n      {\n         if(!this.keybinds.canAct()) return;\n         if(this.keybinds.matches("debug",e))')
    change('            this.dbgOn = !this.dbgOn;',
           '            e.stopImmediatePropagation(); e.preventDefault();\n            this.dbgOn = !this.dbgOn;')
    change('else if(e.keyCode == Keyboard.F11)', 'else if(this.keybinds.matches("toggle",e))')
    change('            this.cfgEnabled = !this.cfgEnabled;',
           '            e.stopImmediatePropagation(); e.preventDefault();\n            this.cfgEnabled = !this.cfgEnabled;')
    change('else if(e.keyCode == Keyboard.F12)\n         {',
           'else if(this.keybinds.matches("mode",e))\n         {\n            e.stopImmediatePropagation(); e.preventDefault();')
    change('else if(e.keyCode == Keyboard.Q)', 'else if(this.keybinds.nativeTeleKey(e))')
    change('      private function onRightDown(e:MouseEvent):void\n      {',
           '      private function onRightDown(e:MouseEvent):void\n      {\n         if(!this.keybinds.canAct() || !this.keybinds.nativeTeleToken("rmb")) return;')
    change('      private function onFrame(e:Event):void\n      {',
           '      private function onFrame(e:Event):void\n      {\n         this.keybinds.tick();')
    change('RVLocale.bind(this.optTxt,txt,true);','RVLocale.bind(this.optTxt,this.keybinds.hint(txt),true);')
    change('RVLocale.bind(this.dbgTxt,msg);','RVLocale.bind(this.dbgTxt,this.keybinds.hint(msg));')
    change('"hint":"总开关（F11 同款）"','"hint":"总开关；快捷键可在本模组的快捷键页修改"')
    if stamp_version:
        change('private static const VERSION:String = "v0.30.5-scene";',
               'private static const VERSION:String = "v0.30.6-keybinds-candidate";')
    return text


def main():
    source = BASE / 'RealisticVisionMod.as'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PIN, 'Installed source lineage changed; inspect first'
    target = OUT / 'src'
    target.mkdir(parents=True, exist_ok=True)
    for path in BASE.rglob('*.as'):
        dest = target / path.relative_to(BASE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    (target / 'RealisticVisionMod.as').write_text(integrate(source.read_text(encoding='utf-8-sig')), encoding='utf-8')
    shutil.copy2(MOD / 'src/RVKeybinds.as', target / 'RVKeybinds.as')
    # Only add the new shortcut phrases to the frozen localization catalog.
    original = (target / 'modlocales/vision/RVLocaleMessages.as').read_text(encoding='utf-8-sig')
    additions = {
        '未绑定': {'en':'Unbound','ru':'Не назначено'},
        '总开关；快捷键可在本模组的快捷键页修改': {
            'en':"Enable vision. Edit its shortcut on this module's Shortcuts page.",
            'ru':'Включить зрение. Клавиша меняется на странице «Клавиши» этого модуля.'},
        '快捷键': {'en':'Shortcuts','ru':'Клавиши'},
        '视野系统 · 快捷键': {'en':'Vision · Shortcuts','ru':'Зрение · Клавиши'},
        '调试显示': {'en':'Debug display','ru':'Отладочная информация'},
        '视野系统总开关': {'en':'Toggle vision','ru':'Переключить зрение'},
        '切换渲染模式': {'en':'Cycle rendering mode','ru':'Сменить режим отображения'},
        '点击当前按键以修改；原有默认键保留。F10与联机浮窗共用时会提示冲突。': {
            'en':'Click a binding to change it. Existing defaults are preserved; shared F10 bindings are marked.',
            'ru':'Нажмите сочетание для изменения. Исходные клавиши сохранены; совпадения F10 отмечены.'}
    }
    anchor = 'public static const DATA:Object = {'
    assert original.count(anchor) == 1
    encoded = json.dumps(additions, ensure_ascii=False, indent=2)[1:-1].strip()
    (target / 'modlocales/vision/RVLocaleMessages.as').write_text(original.replace(anchor, anchor+'\n'+encoded+',\n'), encoding='utf-8')
    sys.path.insert(0, str(MOD / 'build/wall-surface'))
    from run import compile
    binary = OUT / 'candidate/RealisticVisionMod.swf'
    compile(target/'RealisticVisionMod.as', binary, [target], stubs=True)
    receipt = {'version':'0.30.6-keybinds-candidate', 'production_baseline_sha256':PIN,
               'binary':str(binary), 'bytes':binary.stat().st_size,
               'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
               'authority_wip_included':False, 'wall_surface_candidate_included':False,
               'release_modified':False}
    (OUT/'candidate.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
