(function () {
  const names=['overview','body'];
  const tabs=Array.from(document.querySelectorAll('[data-v3-tab]'));
  const panels=Object.fromEntries(names.map(n=>[n,document.getElementById('v3-'+n)]));
  if (!tabs.length || names.some(n=>!panels[n])) return;
  function activate(name, updateHash) {
    if (!names.includes(name)) name='overview';
    for (const n of names) panels[n].hidden=n!==name;
    for (const tab of tabs) {
      const on=tab.dataset.v3Tab===name;
      tab.setAttribute('aria-selected',String(on));
      tab.tabIndex=on?0:-1;
    }
    if(updateHash) history.replaceState(null,'','#'+name);
  }
  tabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>activate(tab.dataset.v3Tab,true));
    tab.addEventListener('keydown',e=>{
      if(!['ArrowRight','ArrowLeft','Home','End'].includes(e.key))return;
      e.preventDefault();
      let next=e.key==='Home'?0:e.key==='End'?tabs.length-1:
        (index+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
      tabs[next].focus();activate(tabs[next].dataset.v3Tab,true);
    });
  });
  document.querySelectorAll('[data-v3-open]').forEach(link=>link.addEventListener('click',e=>{
    e.preventDefault();activate(link.dataset.v3Open,true);
    document.querySelector('.v3-tabs').scrollIntoView({behavior:'smooth',block:'start'});
  }));
  window.addEventListener('hashchange',()=>activate(location.hash.slice(1),false));
  const hasError=!!document.querySelector('.error');
  activate(hasError?'body':location.hash.slice(1),false);
})();
