"""Diagnostic net-memory endpoints; never part of a production build.

Positive deltas are net growth, not allocated bytes. Nested phases overlap.
Collection is process-wide and can occur inside any instrumented phase.
"""
import re


def instrument(source):
    if 'import flash.system.System;' not in source:
        source = source.replace('import flash.display.Bitmap;',
                                'import flash.display.Bitmap;\nimport flash.system.System;')
    pos = source.index('{', source.index('public class')) + 1
    source = source[:pos] + '\npublic var memoryProfile:Object={};\n' + source[pos:]
    names = ['prepareOcclusion', 'computeFov', 'applyVision',
             'updateWallSurface', 'hideEnemies', 'applyWorldVisuals']
    for name in names:
        pattern = r'public function ' + name + r'\(([^)]*)\)\s*:\s*(\w+)\s*\{'
        found = re.search(pattern, source)
        assert found, name
        args, ret = found.group(1), found.group(2)
        params = ','.join(x.strip().split(':')[0] for x in args.split(',') if x.strip())
        replacement = f'''public function {name}({args}):{ret} {{
var memBefore:Number=System.totalMemory, timerBefore:int=getTimer();
{'var result:'+ret+';' if ret != 'void' else ''}
try {{{'result=' if ret != 'void' else ''}memory_{name}({params});}} finally {{
var memDelta:Number=System.totalMemory-memBefore;
var memRow:Object=memoryProfile["{name}"];
if(memRow==null){{memRow={{calls:0,positive:0,negative:0,maxPositive:0,minNegative:0,ms:0}};memoryProfile["{name}"]=memRow;}}
memRow.calls++;memRow.ms+=getTimer()-timerBefore;
if(memDelta>0){{memRow.positive+=memDelta;memRow.maxPositive=Math.max(memRow.maxPositive,memDelta);}}
if(memDelta<0){{memRow.negative+=memDelta;memRow.minNegative=Math.min(memRow.minNegative,memDelta);}}
}}
{'return result;' if ret != 'void' else ''}
}}
public function memory_{name}({args}):{ret} {{'''
        source = source[:found.start()] + replacement + source[found.end():]
    return source
