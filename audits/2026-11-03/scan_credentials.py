"""Read-only, redacted credential-pattern scan of tracked source and reachable Git blobs.
Heuristic patterns are not an assurance that no secret exists. Binary blobs skipped.
"""
from pathlib import Path
import base64,collections,json,re,subprocess
ROOT=Path(__file__).resolve().parents[2]
PATTERNS={
 'stripe_secret':rb'\bsk_(?:live|test)_[A-Za-z0-9]{16,}',
 'stripe_webhook_secret':rb'\bwhsec_[A-Za-z0-9]{16,}',
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',
 'aws_access_id':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
}
JWT=rb'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
def inspect(data):
 counts={kind:len(re.findall(pattern,data)) for kind,pattern in PATTERNS.items()}
 roles=collections.Counter()
 for match in re.finditer(JWT,data):
  try:
   encoded=match.group().split(b'.')[1]
   claims=json.loads(base64.urlsafe_b64decode(encoded+b'='*(-len(encoded)%4)))
   roles[claims.get('role','unspecified')]+=1
  except Exception:pass
 return counts,roles

def main():
 findings=[];roles=collections.Counter()
 for filename in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines():
  data=(ROOT/filename).read_bytes()
  if b'\0' in data[:8192] or data.startswith((b'%PDF',b'\x89PNG')):continue
  counts,r=inspect(data);roles.update(r)
  for kind,count in counts.items():
   if count:findings.append({'file':filename,'kind':kind,'matches':count})
 objects=[line.split()[0] for line in subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT,text=True).splitlines()]
 raw=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=('\n'.join(objects)+'\n').encode(),capture_output=True,check=True).stdout
 cursor=0;counts=collections.Counter();history_roles=collections.Counter();text_blobs=0;binary_blobs=0
 for _ in objects:
  end=raw.index(b'\n',cursor);header=raw[cursor:end].split();size=int(header[2]);cursor=end+1
  data=raw[cursor:cursor+size];cursor+=size+1
  if header[1]!=b'blob':continue
  if b'\0' in data[:8192] or data.startswith((b'%PDF',b'\x89PNG')):binary_blobs+=1;continue
  text_blobs+=1;c,r=inspect(data);counts.update(c);history_roles.update(r)
 print(json.dumps({'redacted':True,'tracked_source_matches':findings,'tracked_jwt_roles':dict(roles),
  'history_text_blobs_scanned':text_blobs,'history_binary_blobs_skipped':binary_blobs,'history_pattern_matches':dict(counts),'history_jwt_roles':dict(history_roles)},indent=2))
if __name__=='__main__':main()
