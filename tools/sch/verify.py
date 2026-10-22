import json, sys, xml.etree.ElementTree as ET
from collections import defaultdict
exp=json.load(open(sys.argv[1])); t=ET.parse(sys.argv[2])
E=defaultdict(set)
for r,v in exp.items():
    for n,net in v['pins'].items():
        if net: E[net].add((r,n))
G={}
for n in t.getroot().iter('net'):
    G[n.get('name')]={(x.get('ref'),x.get('pin')) for x in n.iter('node')}
pinnet={}
for k,v in G.items():
    for rp in v: pinnet[rp]=k
diff=0; total=0
for net,pins in E.items():
    for rp in pins:
        total+=1
        g=pinnet.get(rp,'')
        if g.lstrip('/')!=net and not (g.startswith('Net-') and frozenset(G[g])==frozenset(pins)):
            diff+=1; print('DIFF',rp,'expected',net,'got',g)
print('pins checked',total,'| differences',diff,'| nets expected',len(E),'| nets in schematic',len(G))
