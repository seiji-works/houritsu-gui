#!/usr/bin/env python3
"""Build houritsu GUI prototype from the real downloaded law files.

kojo.md     = current version of the Personal Information Protection Act
kojo_old.md = the version in force until 2022-03-31 (revision enforced 2022-01-01)
Both are real files from Kohei-Wada/houritsu (CC BY 4.0).
"""
import json, re, html, difflib

TARGETS = ["第一条", "第二条", "第三条", "第四条", "第五条", "第六条"]
TITLES = {}

def parse_articles(path):
    """Parse articles 1-6 (main text) out of an houritsu markdown law file."""
    lines = open(path, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## 第一章"))
    arts, cur = {}, None
    for ln in lines[start:]:
        if re.match(r"^#{2,4}\s", ln):
            m = re.match(r"^###\s+(第.+?条)（(.+)）\s*$", ln)
            if m and m.group(1) in TARGETS and m.group(1) not in arts:
                cur = m.group(1)
                arts[cur] = []
                TITLES[cur] = m.group(2)
            elif cur == "第六条":
                break
            else:
                cur = None
            continue
        if cur and ln.strip():
            arts[cur].append(ln.strip())
    return arts

new_arts = parse_articles("kojo.md")
old_arts = parse_articles("kojo_old.md")

articles = []
for no in TARGETS:
    articles.append({"no": no, "title": TITLES.get(no, ""), "text": "\n".join(new_arts[no])})

# plain-language one-liner (our own summary, labelled as such)
summaries = {
    "第一条": "この法律が何のためにあるか、を宣言する条文。",
    "第二条": "「個人情報」「個人識別符号」って何を指すか、を決める条文。",
    "第三条": "個人情報を扱うときの基本的な考え方。",
    "第四条": "国がやるべきことを決めた条文。",
    "第五条": "地方公共団体（都道府県・市区町村）がやるべきこと。",
    "第六条": "必要な法律の整備などを国に求める条文。",
}
for a in articles:
    a["plain"] = summaries.get(a["no"], "")

timeline = [
    ("2026-11-02", "防災庁設置法の施行に伴う関係法律の整備等に関する法律"),
    ("2026-10-01", "日本学術会議法"),
    ("2026-07-17", "防災庁設置法の施行に伴う関係法律の整備等に関する法律"),
    ("2026-07-17", "個人情報の保護に関する法律等の一部を改正する法律"),
    ("2026-06-24", "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律"),
    ("2026-05-21", "民事訴訟法等の一部を改正する法律"),
    ("2025-04-01", "デジタル社会形成基本法等の一部を改正する法律"),
]

# ---------- old vs new comparison ----------
cmp_summaries = {
    "第一条": "「高度情報通信社会」が「デジタル社会」に言い換えられ、行政機関なども対象に入る書き方になりました。個人情報保護委員会を置くことも、目的の中に明記されています。",
    "第二条": "いちばん大きく変わった条です。「仮名加工情報」「個人関連情報」という新しい言葉と、「行政機関」「行政機関等」など役所についての言葉の定義が入りました。反対に「個人データ」「保有個人データ」などの定義は、別の条（第十六条）へ引っ越しました。",
    "第三条": "変わったのは漢字ひとつだけ。「かんがみ」が「鑑み」になりました。",
    "第四条": "国の責務の中身が具体的に書かれるようになりました（国の機関や地方公共団体、独立行政法人などによる個人情報の取扱いを確保すること）。",
    "第五条": "「国の施策との整合性に配慮しつつ」という言葉が加わり、地方公共団体の機関や区域内の事業者など、対象が具体的に書かれるようになりました。",
    "第六条": "この条は、むかしといまで一字も変わりませんでした。",
}

cmp_tags = {
    "第一条": ["趣旨に関わる変更", "字句の言い換え"],
    "第二条": ["構造の変更", "新しい概念の追加", "定義のお引越し"],
    "第三条": ["字句のみ"],
    "第四条": ["内容の具体化"],
    "第五条": ["内容の具体化"],
    "第六条": ["比べた期間では変更なし"],
}
cmp_ronten = {
    "第一条": "対象が民間の事業者中心から、行政機関など公の側にも広がりました。「デジタル社会」を前提にし、監督役の個人情報保護委員会を置くことも目的に明記されています。『何のための法律か』が少し変わった、と言える所です。",
    "第二条": "「仮名加工情報」は、名前などを消して『使えるけれど、誰のものかは分からない』データの扱いを認める考え方です。守ることと活かすことのバランスが論点になります。2022年4月1日には、2つの別の改正法が同じ日にこの条を触っています。同じ条を複数の改正が重なる珍しい例です。",
    "第三条": "意味は変わっていません。漢字の使い方をそろえただけの変更で、こういうものは「形式的な改正」と呼ばれます。",
    "第四条": "2022年と2023年の2回に分けて変わりました。国の仕事の中身が、段階的に具体的に書き込まれていった例です。",
    "第五条": "変わったのは2023年4月から。地方公共団体についての部分は、ほかの部分より1年遅れて始まったことが分かります。",
    "第六条": "比べた期間では一字も変わりませんでした。記録のある範囲（2017年以降）では、2017年に1回だけ変わっています。",
}
try:
    steps_data = json.load(open("steps.json", encoding="utf-8"))["steps"]
except FileNotFoundError:
    steps_data = {}

def esc(s):
    return html.escape(s, quote=False)

def char_diff_html(o, n):
    """Character-level diff of one replaced paragraph, small equal runs absorbed."""
    sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
    ops = [list(op) for op in sm.get_opcodes()]
    # absorb short equal runs between changes so highlights read smoothly
    for i, op in enumerate(ops):
        if op[0] == "equal" and 0 < i < len(ops) - 1 and (op[2] - op[1]) < 6 \
                and ops[i - 1][0] != "equal" and ops[i + 1][0] != "equal":
            op[0] = "change"
    old_out, new_out = [], []
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            old_out.append(esc(o[i1:i2])); new_out.append(esc(n[j1:j2]))
        elif tag == "delete":
            old_out.append('<span class="chg-del">' + esc(o[i1:i2]) + "</span>")
        elif tag == "insert":
            new_out.append('<span class="chg-ins">' + esc(n[j1:j2]) + "</span>")
        else:  # replace or absorbed change
            if i2 > i1:
                old_out.append('<span class="chg-del">' + esc(o[i1:i2]) + "</span>")
            if j2 > j1:
                new_out.append('<span class="chg-ins">' + esc(n[j1:j2]) + "</span>")
    return "".join(old_out), "".join(new_out)

def compare_article(no):
    o, n = old_arts[no], new_arts[no]
    sm = difflib.SequenceMatcher(None, o, n)
    rows, changed = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                t = esc(o[i1 + k])
                rows.append('<div class="cmpRow same"><div class="cmpCell">' + t +
                            '</div><div class="cmpCell">' + t + "</div></div>")
        elif tag == "delete":
            for k in range(i1, i2):
                changed += 1
                rows.append('<div class="cmpRow"><div class="cmpCell delBox">' + esc(o[k]) +
                            '</div><div class="cmpCell none">（いまの版にはありません）</div></div>')
        elif tag == "insert":
            for k in range(j1, j2):
                changed += 1
                rows.append('<div class="cmpRow"><div class="cmpCell none">（むかしの版にはありません）</div>'
                            '<div class="cmpCell insBox">' + esc(n[k]) + "</div></div>")
        else:  # replace: pair paragraphs up, char-diff each pair
            olds, news = o[i1:i2], n[j1:j2]
            for k in range(min(len(olds), len(news))):
                changed += 1
                oh, nh = char_diff_html(olds[k], news[k])
                rows.append('<div class="cmpRow"><div class="cmpCell">' + oh +
                            '</div><div class="cmpCell">' + nh + "</div></div>")
            for k in range(min(len(olds), len(news)), len(olds)):
                changed += 1
                rows.append('<div class="cmpRow"><div class="cmpCell delBox">' + esc(olds[k]) +
                            '</div><div class="cmpCell none">（いまの版にはありません）</div></div>')
            for k in range(min(len(olds), len(news)), len(news)):
                changed += 1
                rows.append('<div class="cmpRow"><div class="cmpCell none">（むかしの版にはありません）</div>'
                            '<div class="cmpCell insBox">' + esc(news[k]) + "</div></div>")
    return {"no": no, "title": TITLES.get(no, ""), "summary": cmp_summaries[no],
            "changed": changed, "html": "".join(rows),
            "tags": cmp_tags.get(no, []), "ronten": cmp_ronten.get(no, ""),
            "steps": steps_data.get(no, [])}

compare = [compare_article(no) for no in TARGETS]

data = {"articles": articles, "timeline": timeline, "compare": compare}
js = "const DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";"

html_doc = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>法令の本棚 — やさしい法令リーダー（試作）</title>
<style>
body{font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;max-width:760px;margin:0 auto;padding:24px 16px 64px;color:#222;line-height:1.8;background:#fdfcf8}
h1{font-size:26px;margin:0 0 4px} .sub{color:#666;font-size:14px;margin-bottom:20px}
input[type=search]{width:100%;font-size:18px;padding:12px;border:2px solid #2a7f62;border-radius:10px;box-sizing:border-box}
.hint{font-size:13px;color:#666;margin:6px 0 20px}
.shelf{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}
.book{border:1px solid #ccc;border-radius:10px;padding:12px 14px;background:#fff;flex:1;min-width:200px;cursor:pointer}
.book.active{border-color:#2a7f62;box-shadow:0 0 0 2px #2a7f6244}
.book h3{margin:0;font-size:17px}.book p{margin:4px 0 0;font-size:13px;color:#555}
.card{background:#fff;border:1px solid #ddd;border-radius:12px;padding:16px 18px;margin:14px 0}
.card h3{margin:0 0 4px;font-size:18px}.plain{color:#2a7f62;font-size:14px;margin:0 0 8px}
.card p{margin:0;font-size:15px;white-space:pre-wrap}
.tl{border-left:3px solid #2a7f62;padding-left:16px;margin:8px 0 8px 4px}
.tl div{margin:10px 0}.tl b{display:block}
.note{font-size:13px;color:#666;background:#f2f0e8;border-radius:8px;padding:12px;margin-top:24px}
footer{font-size:13px;color:#555;border-top:1px solid #ddd;margin-top:32px;padding-top:12px}
a{color:#2a7f62}
.cmpTabs{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.cmpTabs button{font-size:15px;padding:8px 14px;border-radius:999px;border:1px solid #2a7f62;background:#fff;cursor:pointer;font-family:inherit}
.cmpTabs button.active{background:#2a7f62;color:#fff}
.cmpHeads{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-weight:bold;margin:8px 0}
.cmpHeads div{background:#f2f0e8;border-radius:8px;padding:8px 10px;font-size:14px}
.cmpRow{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}
.cmpCell{background:#fff;border:1px solid #ddd;border-radius:10px;padding:10px 12px;font-size:14px;white-space:pre-wrap;word-break:break-all}
.cmpRow.same .cmpCell{color:#777;background:#faf9f5}
.cmpCell.none{color:#999;font-size:13px}
.cmpCell.delBox{background:#fdf0f0}
.cmpCell.insBox{background:#effaf2}
.chg-del{background:#f6c9c9;text-decoration:line-through;border-radius:3px}
.chg-ins{background:#bfe8c8;border-radius:3px}
.badge{display:inline-block;background:#2a7f62;color:#fff;border-radius:999px;padding:2px 12px;font-size:13px;margin:4px 0 8px}
.cmpCtrl{font-size:14px;margin:10px 0}
.legend{background:#f2f0e8;border-radius:8px;padding:12px 14px;font-size:13px;margin:10px 0}
.legend .sw{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin:0 4px 0 10px}
.chip{display:inline-block;border:1px solid #2a7f62;color:#2a7f62;border-radius:999px;padding:1px 10px;font-size:13px;margin:2px 4px 2px 0}
.ronten{background:#fff;border-left:3px solid #c9a227;padding:10px 14px;font-size:14px;margin:14px 0}
.steps{font-size:14px;margin:10px 0}
.steps div{margin:6px 0}
.steps b{color:#2a7f62}
.btnlink{display:inline-block;background:#2a7f62;color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-size:15px}
@media (max-width:640px){.cmpRow,.cmpHeads{grid-template-columns:1fr}}
</style></head><body>
<h1>📚 法令の本棚</h1>
<p class="sub">むずかしい言葉を使わずに、法律を1条ずつ読める試作リーダー</p>
<input type="search" id="q" placeholder="法令名・よみがな・キーワードで探す（例：個人情報、こじん、目的）" aria-label="検索">
<p class="hint">「改正」は「法律が変わったこと」、「本棚」は法令の一覧、という意味で使っています。gitの言葉は画面に出しません。</p>

<div class="shelf" id="shelf"></div>
<h2 id="lawTitle"></h2>
<p id="lawMeta" style="color:#555;font-size:14px"></p>
<div id="cards"></div>

<h2>改正の年表</h2>
<p style="font-size:14px;color:#555">この法律がいつ、どの法律で変わったか。新しい順に7件だけ表示しています。</p>
<div class="tl" id="timeline"></div>

<h2>昔と今を比べる</h2>
<p style="font-size:14px;color:#555">個人情報保護法は2022年4月に大きな改正がありました。その直前（2022年3月まで）の版と、今の版（2026年11月2日から）を並べて比べます。消えた部分は赤、増えた部分は緑で色を付けました。灰色の段落は、むかしも今も同じ文です。</p>
<div class="legend"><b>色の意味</b><span class="sw" style="background:#f6c9c9"></span>赤＝消えた文（むかしにあって、今はない）<span class="sw" style="background:#bfe8c8"></span>緑＝増えた文（今の版で入った）<span class="sw" style="background:#e8e6df"></span>灰色＝変わっていない文<br>色は「変化の大きさ」ではなく、「消えた／増えた」の区別です。何回もの改正を重ねた文でも、色はこの3種類のままです。その条が何回変わったかは、下の「この条が変わった改正」で分かります。</div>
<div class="cmpTabs" id="cmpTabs"></div>
<p class="plain" id="cmpSummary" style="color:#2a7f62;font-size:14px"></p>
<span class="badge" id="cmpBadge"></span>
<div id="cmpTags" style="margin:6px 0"></div>
<div class="cmpCtrl"><label><input type="checkbox" id="cmpOnly"> 変わった所だけ見る</label></div>
<div class="cmpHeads"><div>むかし（2022年3月までの版）</div><div>いま（2026年11月2日からの版）</div></div>
<div id="cmpBody"></div>
<p id="cmpEmpty" style="display:none;color:#666;font-size:14px">この条は変わっていないので、表示する段落がありません。</p>
<div class="ronten" id="cmpRonten"></div>
<h3 style="margin-bottom:4px">この条が変わった改正</h3>
<p style="font-size:13px;color:#555;margin:0">記録のある範囲（2017年以降）で、この条の文章が変わった改正だけを数えました。この法律全体では、この間に30回の改正がありました。</p>
<div class="steps" id="cmpSteps"></div>

<h2>意見・感想を書く</h2>
<p style="font-size:14px;color:#555">この試作への意見や、条文の読み解き・改正についての感想は、意見広場で受け付けています。書くにはGitHubのアカウントが必要です。なお、個別の法的相談にはお答えできません（このサイトは法的助言ではありません）。</p>
<p><a class="btnlink" href="https://github.com/seiji-works/houritsu-gui/discussions">💬 意見広場へ（GitHub Discussions）</a></p>

<div class="note">💡 この試作の読み方：条文のカードには、まず「やさしい一言」（私たちの要約）を置き、その下に条文そのままの文章を載せています。要約は法律そのものではありません。正式な内容は条文で確認してください。なお、このデータの改正の記録は2015年頃からのものが中心です。</div>

<footer>
<strong>出典・クレジット</strong><br>
出典：e-Gov法令検索（法令API）／データ：Kohei-Wada『houritsu』（CC BY 4.0）を加工して使用<br>
条文の文字は変更していません（見出し記号などの表示上の加工を除く）。条文の正本は官報です。法的助言ではありません。<br>
ライセンス：<a href="https://creativecommons.org/licenses/by/4.0/deed.ja">CC BY 4.0</a> ／ 出典規約：<a href="https://www.digital.go.jp/resources/open_data/public_data_license_v1.0">公共データ利用規約（第1.0版）</a><br>
元データ：<a href="https://github.com/Kohei-Wada/houritsu">github.com/Kohei-Wada/houritsu</a>
</footer>
<script>
""" + js + """
const laws=[
 {title:"個人情報の保護に関する法律",kana:"こじんじょうほうのほごにかんするほうりつ",abbr:"個人情報保護法",num:"平成十五年法律第五十七号",rev:"最新：令和八年法律第六十二号（2026-11-02施行）",ready:true},
 {title:"民法",kana:"みんぽう",abbr:"",num:"明治二十九年法律第八十九号",rev:"最新：令和八年法律第四十五号（2026-06-24施行）",ready:false},
 {title:"刑法",kana:"けいほう",abbr:"",num:"明治四十年法律第四十五号",rev:"最新：令和七年法律第三十九号（2025-05-21施行）",ready:false}
];
let current=0;
const shelf=document.getElementById('shelf');
laws.forEach((l,i)=>{
 const d=document.createElement('div');d.className='book'+(i===0?' active':'');
 d.innerHTML='<h3>'+l.title+'</h3><p>'+l.num+'<br>'+l.rev+'</p>'+(l.ready?'':'<p>※ 本文はまだこの試作に入っていません</p>');
 d.onclick=()=>{current=i;document.querySelectorAll('.book').forEach((b,j)=>b.classList.toggle('active',j===i));render();};
 shelf.appendChild(d);
});
function render(){
 const l=laws[current];
 document.getElementById('lawTitle').textContent=l.title;
 document.getElementById('lawMeta').textContent=l.num+' ／ '+l.rev+' ／ 全206条（この試作は第一章・第1条〜第6条のみ）';
 const q=(document.getElementById('q').value||'').trim();
 const box=document.getElementById('cards');box.innerHTML='';
 if(!l.ready){box.innerHTML='<p>この法令の本文は、試作の次の段階で追加します。上のカードの「最新」情報は、houritsuの実データ（frontmatter）から取ったものです。</p>';return;}
 DATA.articles.filter(a=>!q||(a.no+a.title+a.plain+a.text).includes(q)).forEach(a=>{
   const c=document.createElement('div');c.className='card';
   c.innerHTML='<h3>'+a.no+'（'+a.title+'）</h3><p class="plain">やさしい一言：'+a.plain+'</p><p></p>';
   c.querySelector('p:last-child').textContent=a.text;
   box.appendChild(c);
 });
 if(!box.children.length)box.innerHTML='<p>見つかりませんでした。別の言葉で探してみてください。</p>';
}
document.getElementById('timeline').innerHTML=DATA.timeline.map(t=>'<div><b>'+t[0]+' 施行</b>'+t[1]+'</div>').join('');
document.getElementById('q').addEventListener('input',render);
render();

// ---- old vs new comparison ----
let cmpIdx=0;
const cmpTabs=document.getElementById('cmpTabs');
DATA.compare.forEach((c,i)=>{
 const b=document.createElement('button');
 b.textContent=c.no;
 b.className=i===0?'active':'';
 b.onclick=()=>{cmpIdx=i;renderCmp();};
 cmpTabs.appendChild(b);
});
function renderCmp(){
 const c=DATA.compare[cmpIdx];
 document.getElementById('cmpSummary').textContent='やさしい一言：'+c.summary;
 document.getElementById('cmpBody').innerHTML=c.html;
 document.querySelectorAll('#cmpTabs button').forEach((b,j)=>b.classList.toggle('active',j===cmpIdx));
 document.getElementById('cmpBadge').textContent=c.changed?('変わった段落：'+c.changed+'か所'):'この条は変わりませんでした';
 document.getElementById('cmpTags').innerHTML=(c.tags||[]).map(t=>'<span class="chip">'+t+'</span>').join('');
 const rt=document.getElementById('cmpRonten');
 rt.textContent=c.ronten?('読み解きメモ（私たちの解釈です）：'+c.ronten):'';
 rt.style.display=c.ronten?'':'none';
 const st=document.getElementById('cmpSteps');st.innerHTML='';
 if(c.steps&&c.steps.length){
   const h=document.createElement('div');
   h.innerHTML='<b>'+c.steps.length+'回</b> 変わりました';
   st.appendChild(h);
   c.steps.forEach(s=>{
     const d=document.createElement('div');
     const b=document.createElement('b');b.textContent=s.date+' 施行';
     d.appendChild(b);d.appendChild(document.createTextNode('　'+s.law));
     st.appendChild(d);
   });
 }else{
   st.innerHTML='<div>記録のある範囲では、この条が変わった改正はありません。</div>';
 }
 applyCmpFilter();
}
function applyCmpFilter(){
 const only=document.getElementById('cmpOnly').checked;
 let visible=0;
 document.querySelectorAll('#cmpBody .cmpRow').forEach(r=>{
   const hide=only&&r.classList.contains('same');
   r.style.display=hide?'none':'';
   if(!hide)visible++;
 });
 document.getElementById('cmpEmpty').style.display=(only&&visible===0)?'':'none';
}
document.getElementById('cmpOnly').addEventListener('change',applyCmpFilter);
renderCmp();
</script></body></html>
"""
open("index.html", "w", encoding="utf-8").write(html_doc)
print("articles:", len(articles), [a["no"] for a in articles])
print("timeline entries:", len(timeline))
print("compare changed counts:", {c["no"]: c["changed"] for c in compare})
print("html bytes:", len(html_doc))
