import decision as BG

cues = [0, 1]
positions = [2, 0]
cog, mot = BG.choose(cues, positions, bias=True)
print 'choosen ', cog, ' at ', mot
