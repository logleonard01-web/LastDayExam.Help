(function(){
var btn=document.querySelector('.menu-btn'),nav=document.getElementById('nav-list');
if(btn&&nav){btn.addEventListener('click',function(){var o=nav.classList.toggle('open');btn.setAttribute('aria-expanded',o?'true':'false');});}

/* vocabulary filter */
var vq=document.querySelector('[data-vocab-q]'),vs=document.querySelector('[data-vocab-s]');
if(vq&&vs){
  var items=[].slice.call(document.querySelectorAll('li[data-subject]'));
  var secs=[].slice.call(document.querySelectorAll('[data-letter]'));
  var st=document.getElementById('vocab-status'),empty=document.getElementById('vocab-empty');
  var run=function(){
    var q=vq.value.trim().toLowerCase(),s=vs.value,n=0;
    items.forEach(function(li){
      var ok=(!s||li.dataset.subject===s)&&(!q||li.dataset.text.indexOf(q)>-1);
      li.hidden=!ok;if(ok)n++;
    });
    secs.forEach(function(sec){sec.hidden=!sec.querySelector('li:not([hidden])');});
    st.textContent=(q||s)?n+' term'+(n===1?'':'s')+' shown':'';
    empty.hidden=n>0;
  };
  vq.addEventListener('input',run);vs.addEventListener('change',run);
  var p=new URLSearchParams(location.search).get('q');if(p){vq.value=p;run();}
}

/* site search */
var box=document.getElementById('results');
if(box){
  var more=document.getElementById('more'),status=document.getElementById('search-status');
  var sq=document.getElementById('sq'),hdr=document.getElementById('q');
  var q=(new URLSearchParams(location.search).get('q')||'').trim();
  if(sq)sq.value=q;if(hdr)hdr.value=q;
  var hits=[],shown=0,PAGE=20;
  var render=function(){
    var ul=box.querySelector('ul');
    if(!ul){ul=document.createElement('ul');ul.className='cards';box.appendChild(ul);}
    hits.slice(shown,shown+PAGE).forEach(function(h){
      var li=document.createElement('li'),a=document.createElement('a'),b=document.createElement('strong'),s=document.createElement('span'),t=document.createElement('em');
      a.href=h.u;b.textContent=h.t;a.appendChild(b);s.textContent=h.d;t.className='tag';t.textContent=h.k;
      li.appendChild(a);li.appendChild(s);li.appendChild(t);ul.appendChild(li);
    });
    shown=Math.min(hits.length,shown+PAGE);more.hidden=shown>=hits.length;
  };
  if(!q){status.textContent='Type a word or phrase above to search.';}
  else{
    status.textContent='Searching…';
    fetch('/assets/search-index.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(idx){
      var w=q.toLowerCase().split(/\s+/).filter(Boolean);
      idx.forEach(function(i){
        var t=i.t.toLowerCase(),h=(i.h||'').toLowerCase(),d=i.d.toLowerCase(),score=0,ok=true;
        w.forEach(function(x){
          var sc=0;
          if(t===x)sc=100;else if(t.indexOf(x)===0)sc=60;else if(t.indexOf(x)>-1)sc=40;
          else if(h.indexOf(x)>-1)sc=15;else if(d.indexOf(x)>-1)sc=8;
          if(!sc)ok=false;score+=sc;
        });
        if(ok){i.s=score;hits.push(i);}
      });
      hits.sort(function(a,b){return b.s-a.s||a.t.localeCompare(b.t);});
      if(!hits.length){status.textContent='No results for “'+q+'”. Try a shorter or different word, or browse the subjects and vocabulary.';return;}
      status.textContent=hits.length+' result'+(hits.length===1?'':'s')+' for “'+q+'”';
      render();more.addEventListener('click',render);
    }).catch(function(){status.textContent='Search is unavailable right now. Please browse the subjects or vocabulary instead.';});
  }
}
})();
