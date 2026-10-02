
(function(){
  var tip=document.getElementById('ds-tip');
  // ポータルの「緊急」印：期限（公表日から7日間）を過ぎたら隠す
  var now=new Date(Date.now()+9*3600*1000).toISOString().slice(0,10);
  [].slice.call(document.querySelectorAll('.ed-alert[data-until]')).forEach(function(el){if(now>el.getAttribute('data-until'))el.setAttribute('data-expired','');});
  // データソース：ポータルの上にポップアップで出す（ボタンが無いページでは何もしない）
  var dsOpen=document.getElementById('ds-open'),dsm=document.getElementById('dsm'),dsb=document.getElementById('dsm-body'),lastFocus=null;
  if(dsOpen&&dsm){
    var openM=function(){lastFocus=document.activeElement;dsm.hidden=false;document.documentElement.classList.add('dsm-open');if(dsb)dsb.scrollTop=0;document.getElementById('dsm-x').focus();};
    var closeM=function(){dsm.hidden=true;document.documentElement.classList.remove('dsm-open');if(tip)tip.hidden=true;if(lastFocus&&lastFocus.focus)lastFocus.focus();};
    dsOpen.addEventListener('click',function(e){e.preventDefault();openM();});
    [].slice.call(dsm.querySelectorAll('[data-close]')).forEach(function(el){el.addEventListener('click',closeM);});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!dsm.hidden)closeM();});
    if(dsb)dsb.addEventListener('scroll',function(){if(tip)tip.hidden=true;});
  }
  var scope=dsm||document;
  // ページごとの参照先
  var pbs=[].slice.call(scope.querySelectorAll('.pgb'));
  function pick(k){if(!document.getElementById('pg-'+k))k='news';pbs.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-k')===k?'true':'false');});[].slice.call(scope.querySelectorAll('.pgp')).forEach(function(p){p.hidden=(p.id!=='pg-'+k);});}
  pbs.forEach(function(b){b.addEventListener('click',function(){pick(b.getAttribute('data-k'));});});
  if(!dsm){var hh=(location.hash||'').slice(1);if(hh)pick(hh);}
  // 一覧の絞り込み
  var dq=document.getElementById('ds-q'),gsel='';
  if(dq){
    var drows=[].slice.call(scope.querySelectorAll('.dsr')),dgroups=[].slice.call(scope.querySelectorAll('.dsg'));
    var dfilter=function(){var q=(dq.value||'').trim().toLowerCase(),n=0;drows.forEach(function(r){var ok=(!gsel||r.getAttribute('data-g')===gsel)&&(!q||r.getAttribute('data-text').toLowerCase().indexOf(q)>=0);r.hidden=!ok;if(ok)n++;});dgroups.forEach(function(g){var v=[].filter.call(g.querySelectorAll('.dsr'),function(r){return !r.hidden;}).length;g.hidden=v===0;g.querySelector('.dsg-h span').textContent=v+'件';});document.getElementById('ds-count').textContent=n+'件を表示';document.getElementById('ds-empty').hidden=n>0;};
    dq.addEventListener('input',dfilter);
    [].slice.call(scope.querySelectorAll('.dsc')).forEach(function(b){b.addEventListener('click',function(){gsel=b.getAttribute('data-g');[].slice.call(scope.querySelectorAll('.dsc')).forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});dfilter();});});
  }
  // 横棒のツールチップ
  function showTip(el,x,y){if(!tip)return;var p=el.getAttribute('data-tip').split('｜');tip.innerHTML='<b>'+p[0]+'</b>　'+p[1]+'<br>'+p.slice(2).join('・');tip.hidden=false;var w=tip.offsetWidth,h=tip.offsetHeight;tip.style.left=Math.max(8,Math.min(x+14,window.innerWidth-w-8))+'px';tip.style.top=Math.max(8,y-h-10)+'px';}
  [].slice.call(scope.querySelectorAll('.dsb,.pgr')).forEach(function(el){el.addEventListener('mousemove',function(e){showTip(el,e.clientX,e.clientY);});el.addEventListener('mouseleave',function(){if(tip)tip.hidden=true;});el.addEventListener('focus',function(){var r=el.getBoundingClientRect();showTip(el,r.left+r.width*0.5,r.top);});el.addEventListener('blur',function(){if(tip)tip.hidden=true;});});
})();
