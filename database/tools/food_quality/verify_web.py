"""Compile JSP and run isolated Chrome fixtures; JspC can return exit0 even on errors."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from build_provenance import ROOT


def verify(jdk,tomcat,chrome):
    out=ROOT/'target/food-quality';out.mkdir(exist_ok=True)
    m2=Path.home()/'.m2/repository/org/apache/ant'
    cp=';'.join([str(tomcat/'bin/tomcat-juli.jar'),str(tomcat/'lib/*'),str(m2/'ant/1.10.15/ant-1.10.15.jar'),str(m2/'ant-launcher/1.10.15/ant-launcher-1.10.15.jar'),'target/nutrifit/WEB-INF/classes','target/nutrifit/WEB-INF/lib/*'])
    p=subprocess.run([str(jdk/'bin/java.exe'),'-cp',cp,'org.apache.jasper.JspC','-uriroot','target/nutrifit','-d','target/jsp-quality','-compile'],cwd=ROOT,capture_output=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    log=(p.stdout+p.stderr).decode('utf-8',errors='replace');(out/'jsp-compile.log').write_text(log,encoding='utf-8')
    if p.returncode or 'Generation completed with [0] errors' not in log or re.search(r'Error count: \[[1-9]',log):
        raise ValueError('JSP compile failed; inspect target/food-quality/jsp-compile.log')
    print('JSP PASS:0 errors')
    results=[]
    for name in ['nutrition-ui-test','nutrition-swap-ui-test']:
        args=[str(chrome),'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions','--allow-file-access-from-files','--user-data-dir='+str(out/(name+'-profile')),'--dump-dom','--virtual-time-budget=3500',(ROOT/'src/test/resources'/(name+'.html')).as_uri()]
        p=subprocess.run(args,capture_output=True,timeout=55,creationflags=subprocess.CREATE_NO_WINDOW)
        (out/(name+'-dom.html')).write_bytes(p.stdout)
        text=p.stdout.decode('utf-8',errors='replace');m=re.search(r'<pre id="result">([^<]*)</pre>',text)
        result=m.group(1) if m else 'NO_RESULT';print(name,p.returncode,result)
        if p.returncode or not result.startswith('PASS '):raise ValueError('Browser fixture failed '+name+':'+result)
        results.append(dict(fixture=name,result=result,status='PASS'))
    report=dict(status='PASS',jsp_errors=0,browser_tests=results)
    (out/'web-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--jdk',type=Path,required=True);p.add_argument('--tomcat',type=Path,required=True);p.add_argument('--chrome',type=Path,required=True)
    a=p.parse_args();verify(a.jdk,a.tomcat,a.chrome)
