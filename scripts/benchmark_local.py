"""Bounded sequential local HTTP benchmark with actual authentication, no save/load test.
Credentials are inherited via process env only. Not a production benchmark tool.
"""
import argparse,http.cookiejar,json,math,os,re,shutil,socket,statistics,subprocess,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--setup',action='store_true');p.add_argument('--samples',type=int,default=25);p.add_argument('--fixture-index',type=int,choices=[0,2],default=0);p.add_argument('--war',type=Path);p.add_argument('--include-workout-plan',action='store_true');a=p.parse_args()
 if not re.fullmatch('[a-z0-9-]+',a.label) or not 10<=a.samples<=40:raise ValueError('Invalid limits')
 if os.environ.get('NUTRIFIT_LOCAL_DB_NAME')!='nutrifit_performance_20261020_test' or os.environ.get('NUTRIFIT_DB_URL','').strip():raise ValueError('Approved isolated local target required')
 jdk=Path(os.environ['JAVA_HOME']);tc=Path(os.environ['TOMCAT_HOME']);out=ROOT/'target/performance'/a.label;out.mkdir(parents=True,exist_ok=False)
 env=os.environ.copy();env['NUTRIFIT_PERF_ENABLED']='true'
 if not env.get('NUTRIFIT_BENCH_PASSWORD'):raise ValueError('Parent must supply temporary benchmark password')
 cp='target/test-classes;target/classes;target/nutrifit/WEB-INF/lib/*'
 if a.setup:subprocess.run([str(jdk/'bin/java.exe'),'-cp',cp,'com.nutrifit.performance.LocalPerformanceCheck','setup'],cwd=ROOT,env=env,check=True)
 subprocess.run([str(jdk/'bin/java.exe'),'-cp',cp,'com.nutrifit.performance.LocalPerformanceCheck','inspect'],cwd=ROOT,env=env,check=True)
 base=out/'tomcat';(base/'conf').mkdir(parents=True)
 for n in ['web.xml','catalina.properties','logging.properties']:shutil.copy2(tc/'conf'/n,base/'conf'/n)
 for n in ['webapps','logs','temp','work']:(base/n).mkdir()
 (base/'conf/server.xml').write_text('<Server port="-1"><Service name="Catalina"><Connector address="127.0.0.1" port="9088" protocol="HTTP/1.1"/><Engine name="Catalina" defaultHost="localhost"><Host name="localhost" appBase="webapps" unpackWARs="true" autoDeploy="false"/></Engine></Service></Server>')
 shutil.copy2(a.war if a.war else ROOT/'target/nutrifit.war',base/'webapps/nutrifit.war')
 with socket.socket() as s:s.bind(('127.0.0.1',9088))
 log=(out/'server.log').open('wb')
 proc=subprocess.Popen([str(jdk/'bin/java.exe'),'-Dfile.encoding=UTF-8','-Duser.timezone=Asia/Ho_Chi_Minh','-Dcatalina.home='+str(tc),'-Dcatalina.base='+str(base),'-Djava.io.tmpdir='+str(base/'temp'),'-cp',str(tc/'bin/bootstrap.jar')+';'+str(tc/'bin/tomcat-juli.jar'),'org.apache.catalina.startup.Bootstrap','start'],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),NoRedirect())
 def request(path,data=None,extra_headers=None):
  req=urllib.request.Request('http://127.0.0.1:9088/nutrifit'+path,data=None if data is None else urllib.parse.urlencode(data).encode(),headers={'Connection':'close',**(extra_headers or {})});start=time.perf_counter()
  try:resp=client.open(req,timeout=35)
  except urllib.error.HTTPError as e:resp=e
  with resp:return resp.code,resp.headers,resp.read().decode('utf-8'),(time.perf_counter()-start)*1000
 try:
  for i in range(100):
   if proc.poll() is not None:raise RuntimeError('Tomcat exited; inspect local log')
   try:
    if request('/health')[0]==200:break
   except OSError:pass
   time.sleep(.4)
  else:raise RuntimeError('Startup timeout')
  code,_,body,_=request('/login');assert code==200
  token=re.search(r'name="_csrf"\s+value="([^"]+)"',body).group(1)
  assert request('/login',dict(email='performance-'+str(a.fixture_index)+'@example.invalid',password=env['NUTRIFIT_BENCH_PASSWORD'],_csrf=token))[0]==302
  results={};cold={}
  for route in ['/dashboard','/nutrition/recommendations','/workout','/profile']+(['/workout/plan'] if a.include_workout_plan else []):
   cold[route]=request(route)[3]
   for i in range(5):assert request(route)[0]==200
   values=[]
   for i in range(a.samples):
    code,h,_,elapsed=request(route);assert code==200,(route,code);assert h.get('Cache-Control')=='no-store';values.append(elapsed)
   results[route]=dict(n=len(values),median_ms=round(statistics.median(values),3),p95_ms=round(sorted(values)[math.ceil(.95*len(values))-1],3),errors=0)
  _,_,body,_=request('/nutrition/recommendations');csrf=re.search(r'name="csrfToken"\s+value="([^"]+)"',body).group(1)
  for action in ['regenerate','swap']:
   values=[]
   for i in range(10):
    _,_,body,_=request('/nutrition/recommendations');token=re.search(r'name="suggestionToken"\s+value="([^"]+)"',body).group(1)
    code,_,_,elapsed=request('/nutrition/recommendations',dict(action=action,csrfToken=csrf,suggestionToken=token,mealType='BREAKFAST',format='json'));assert code in (200,302),(action,code);values.append(elapsed)
   results[action]=dict(n=10,median_ms=round(statistics.median(values),3),p95_ms=round(max(values),3),errors=0)
  code,h,_,_=request('/assets/css/dashboard.css');assert code==200
  report=dict(label=a.label,environment='local Tomcat10.1/JDK21/loopback MySQL; real login; sequential; instrumented',cold_first_route_ms=cold,routes=results,static_cache_control=h.get('Cache-Control'),static_etag=h.get('ETag'))
  # Conditional revalidation and deployment-versioned static URLs are checked after timing.
  etag=h.get('ETag')
  if etag:assert request('/assets/css/dashboard.css',extra_headers={'If-None-Match':etag})[0]==304
  _,_,page,_=request('/dashboard')
  version=re.search(r'/assets/css/dashboard.css\?v=([^"<> ]+)',page)
  if version:
   _,cache,_,_=request('/assets/css/dashboard.css?v='+version.group(1));assert 'immutable' in cache.get('Cache-Control','')
  assert request('/admin')[0]==403
  assert request('/payment')[0]==200
  (out/'http.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
 finally:
  proc.terminate()
  try:proc.wait(timeout=12)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  log.close()
 lines=(out/'server.log').read_text(encoding='utf-8',errors='replace').splitlines();timings=[line[line.index('perf route='):] for line in lines if 'perf route=' in line]
 (out/'timings.log').write_text('\n'.join(timings)+'\n',encoding='utf-8');print('PASS bounded local authenticated benchmark; no journal saves')
if __name__=='__main__':main()
