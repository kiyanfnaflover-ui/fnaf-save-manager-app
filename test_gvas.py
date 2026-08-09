import os, sys
sys.path.insert(0, 'C:/Users/Lion/Desktop/fnaf_save_manager')
from core.gvas_parser import GvasSave

path = os.path.join(os.environ['LOCALAPPDATA'], 'freddys', 'Saved', 'SaveGames', 'Player00.sav')
g = GvasSave(path).load()
print('parse OK  file=%d  none@%d' % (len(g.data), g.none_pos))
for p in g.props:
    if 'value' in p and p['type'] != 'MapProperty':
        v = p['value']
        if p['type'] == 'SetProperty' and p['name'] == 'ObjectsEaten':
            v = '(%d objects)' % len(v)
        print('  %-28s %-13s size=%-5d value=%r' % (p['name'], p['type'], p['size'], v))

# no-op round trip must be byte-identical
noop = g.build(g.data, g.props, g.none_pos)
print('no-op identical:', noop == g.data)

# full edit round trip on a temp copy
g.set('CollectedCoins', list(range(1, 51)))
g.set('CollectedGlitches', list(range(1, 17)))
g.set('NumberOfGamesWon', 0)
g.set('NumberOfGamesLost', 0)
g.set('DarkRideHighScore', 99999)
g.set('HasPlayedMenuInstructions', 1)
g.write()
g2 = GvasSave('x').parse(g.data)
print('edit reparse OK  newlen=%d' % len(g.data))
for p in g2[0]:
    if p['name'] in ('CollectedCoins','CollectedGlitches','NumberOfGamesWon','DarkRideHighScore'):
        print('  %s = %r' % (p['name'], p['value']))

# save compact copy for manual inspect
out = 'C:/Users/Lion/AppData/Local/Temp/opencode/Player00_edited2.sav'
g.save(out)
print('wrote', out)