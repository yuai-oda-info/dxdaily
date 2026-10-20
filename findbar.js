/* MediKoto findbar v2（2026-10-20）：各ページの検索バーで、ページを移動せずにその場で全ページ・全号の本文を検索する。
   旧 findbar v1 は Enter でトップ（#q=）へ移動していた。v1 のスクリプトは各ページに残っているが、
   ここで input／keydown を先に受け取って止めるので、v1 は動かない。
   本文データはトップと同じ search-data.json（サイト直下）を、最初に検索したときに1回だけ読む。 */
(function(){
  var inp=document.getElementById('mkq'), out=document.getElementById('mkf-out');
  if(!inp||!out||inp.dataset.fb2){return;}
  inp.dataset.fb2='1';
  var PG={news:['ヘッドライン','news'],study:['勉強会','study'],nursing:['看護','nursing'],doctors:['医師','doctors'],
    pharm:['薬剤師','pharm'],connect:['相談支援・連携','connect'],se:['病院SE','hospitalit'],nutrition:['栄養','nutrition'],
    care:['介護職','care'],admin:['医事・事務','office'],rehab:['リハビリ','rehab'],tech:['医療技術','medtech'],
    reim:['診療報酬','reimbursement'],global:['海外DX','global']};
  var PER=20;
  var TH={};try{var SL=JSON.parse((document.getElementById('search-lite')||{}).textContent||'[]');for(var z=0;z<SL.length;z++){TH[SL[z][0]+'|'+SL[z][2]]=SL[z][3];}}catch(e){}
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function rx(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
  function jp(d){var p=d.split('-');return (+p[0])+'年'+(+p[1])+'月'+(+p[2])+'日';}
  var data=null, loading=null, failed=false, shown=PER, timer=null;
  function load(){
    if(data||failed){return Promise.resolve();}
    if(!loading){
      loading=fetch('search-data.json',{cache:'no-cache'}).then(function(r){if(!r.ok){throw 0;}return r.json();})
        .then(function(S){data=[];for(var i=0;i<S.length;i++){var e=S[i],k=e.k||'news';if(!PG[k]||!e.d){continue;}
          var x=e.x||'';data.push({d:e.d,k:k,x:x,l:x.toLowerCase()});}
          data.sort(function(a,b){return a.d<b.d?1:(a.d>b.d?-1:0);});})
        .catch(function(){failed=true;});
    }
    return loading;
  }
  function hi(t,terms){for(var i=0;i<terms.length;i++){try{t=t.replace(new RegExp(rx(esc(terms[i])),'gi'),function(m){return '<mark>'+m+'</mark>';});}catch(e){}}return t;}
  function render(){
    var q=inp.value.replace(/　/g,' ').trim();
    if(!q){out.innerHTML='';return;}
    if(!data){
      if(failed){out.innerHTML='<p class="mkf-none">このページでは本文検索のデータを読み込めませんでした。</p>';return;}
      out.innerHTML='<p class="mkf-none">本文データを読み込んでいます…</p>';load().then(render);return;
    }
    var terms=q.split(/\s+/).filter(function(s){return s;}), lows=terms.map(function(s){return s.toLowerCase();});
    var hits=[];
    for(var i=0;i<data.length;i++){var ok=true;for(var j=0;j<lows.length;j++){if(data[i].l.indexOf(lows[j])<0){ok=false;break;}}if(ok){hits.push(data[i]);}}
    if(!hits.length){out.innerHTML='<p class="mkf-none">「'+esc(q)+'」に一致する記事は見つかりませんでした。キーワードを短くしてお試しください。</p>';return;}
    var lis=[];
    for(var k=0;k<hits.length&&k<shown;k++){
      var h=hits[k], pos=h.l.indexOf(lows[0]), st=pos<0?0:Math.max(0,pos-30), sn=h.x.substr(st,120);
      var url=PG[h.k][1]+'-'+h.d+'.html';
      lis.push('<li><a href="'+esc(url)+'"><span class="mkf-tag" data-k="'+esc(h.k)+'">'+esc(PG[h.k][0])+'</span>'
        +'<span class="mkf-d">'+esc(jp(h.d))+'</span><span class="mkf-th">'+esc(TH[h.d+'|'+h.k]||(PG[h.k][0]+'のページ'))+'</span></a>'
        +'<span class="mkf-sn">…'+hi(esc(sn),terms)+'…</span></li>');
    }
    var more=hits.length>shown?'<button type="button" class="mkf-more">さらに'+Math.min(PER,hits.length-shown)+'件を表示（残り'+(hits.length-shown)+'件）</button>':'';
    out.innerHTML='<p class="mkf-cnt">'+hits.length+'件が見つかりました（新しい順）。</p><ul>'+lis.join('')+'</ul>'+more
      +'<button type="button" class="mkf-clear">検索結果を閉じる</button>';
  }
  /* v1 のハンドラより先に受け取り、ページ移動を止める */
  document.addEventListener('input',function(e){if(e.target!==inp){return;}e.stopImmediatePropagation();shown=PER;clearTimeout(timer);timer=setTimeout(render,200);},true);
  document.addEventListener('keydown',function(e){if(e.target!==inp||e.key!=='Enter'){return;}e.preventDefault();e.stopImmediatePropagation();shown=PER;clearTimeout(timer);render();},true);
  inp.addEventListener('focus',function(){load();},{once:true});
  out.addEventListener('click',function(e){
    var t=e.target;
    if(t.closest&&t.closest('.mkf-more')){shown+=PER;render();}
    else if(t.closest&&t.closest('.mkf-clear')){inp.value='';out.innerHTML='';inp.focus();}
  });
  var hint=document.querySelector('#mkfind .mkf-hint');
  if(hint){hint.textContent='ヘッドライン・勉強会・職種別・診療報酬・海外DXの全ページ・全ての号の本文から、このページのまま探せます。スペース区切りで絞り込み。';}
  var css=document.createElement('style');
  css.textContent='#mkf-out .mkf-cnt{font-size:.78rem;color:var(--mut,#7C8A94);margin:.4rem 0 .2rem}'
    +'#mkf-out ul{max-height:min(60vh,34rem);overflow-y:auto;overscroll-behavior:contain;margin:0;padding:0;list-style:none}'
    +'#mkf-out li{padding:.45rem 0;border-bottom:1px dashed var(--rule,#D9DDE0)}'
    +'#mkf-out .mkf-sn{display:block;font-size:.76rem;line-height:1.7;color:var(--sub,#4A5A66);margin-top:.15rem}'
    +'#mkf-out mark{background:#FFF1A8;color:inherit;padding:0 .05em}'
    +'#mkf-out .mkf-more,#mkf-out .mkf-clear{font:inherit;font-size:.8rem;font-weight:700;margin:.55rem .8rem 0 0;padding:.25rem .8rem;border:1px solid var(--rule,#D9DDE0);background:transparent;color:var(--teal,#007C76);cursor:pointer}'
    +'@media (prefers-color-scheme:dark){#mkf-out mark{background:#5A4B10}}';
  document.head.appendChild(css);
})();
