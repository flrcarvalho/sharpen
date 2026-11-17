import json,sys,os,collections,re
rows={}
for f in os.listdir(sys.argv[1]):
    if not f.startswith('http_'): continue
    for ln in open(os.path.join(sys.argv[1],f),encoding='utf-8',errors='replace'):
        try: r=json.loads(ln); rows[r['requestId']]=r
        except: pass
rows=list(rows.values())
def norm(p):
    p=p.split('?')[0]
    p=re.sub(r'/[A-Za-z0-9_-]{20,}','/:id',p); p=re.sub(r'/\d+','/:n',p)
    return p
tot=collections.Counter(); err=collections.Counter(); st=collections.Counter()
for r in rows:
    k=(r['method'],norm(r['path'])); tot[k]+=1; s=r['httpStatus']; st[s]+=1
    if s>=400: err[(k,s)]+=1
print('requisicoes',len(rows),'status',sorted(st.items()))
for (k,s),n in sorted(err.items(),key=lambda x:-x[1]): print(n,'/',tot[k],s,*k)
print('--- ips dos 426/413/5xx')
for r in sorted(rows,key=lambda r:r['timestamp']):
    if r['httpStatus'] in (413,426) or r['httpStatus']>=500: print(r['timestamp'][:19],r['httpStatus'],r['method'],norm(r['path']),r['srcIp'],r['totalDuration'],r.get('responseDetails',''))
