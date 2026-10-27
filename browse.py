"""
Dataset browser section for the portal pages: reads datasets.jsonl (and fields.jsonl).

Used by report.py; it has no command line of its own.
    build_data(host, base, jsonl_path, fields_path, stats) -> dict
    js_file(data)  -> text of <out>/<host>-datasets.js
    rss(data)      -> text of <out>/<host>.rss.xml (recently updated datasets)
    section(host)  -> HTML of the section; CSS and JS are the styles and script

The same input gives the same bytes: the clock is never used.
Spec: docs/specs/P7-dataset-browser.md. Standard library only.
"""
import html
import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import quote

NOTES_MAX = 300
NAME_MAX = 120
FEED_MAX = 50
OK_STATUS = "ok"


# ---------------------------------------------------------------- data helpers

def norm_format(value):
    f = (value or "").strip().upper().lstrip(".")
    return f or "?"


def to_size(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def day(value):
    return (value or "")[:10]


def embed_json(obj):
    """JSON for a <script> element; '<' is escaped."""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def read_fields(path):
    """resource_id -> record, for records with status ok."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("status") == OK_STATUS:
                out[rec.get("resource_id")] = rec
    return out


def slim_resource(r, fields):
    rid = r.get("id") or ""
    out = {"name": (r.get("name") or "")[:NAME_MAX], "fmt": norm_format(r.get("format")),
           "size": to_size(r.get("size")), "created": day(r.get("created")),
           "ds": bool(r.get("datastore_active"))}
    rec = fields.get(rid)
    if rec is not None:
        out["fields"] = [[f.get("id", ""), f.get("type", "")] for f in rec.get("fields", [])
                         if f.get("id") != "_id"]
        out["total"] = rec.get("total")
    return out


def slim_dataset(p, fields, stat):
    org = p.get("organization") or {}
    d = {
        "name": p.get("name") or "",
        "title": p.get("title") or p.get("name") or "",
        "org": org.get("name") or "",
        "created": day(p.get("metadata_created")),
        "modified": day(p.get("metadata_modified")),
        "license": p.get("license_title") or p.get("license_id") or "",
        "tags": [t.get("name") for t in (p.get("tags") or []) if t.get("name")],
        "notes": (p.get("notes") or "")[:NOTES_MAX],
        "res": [slim_resource(r, fields) for r in (p.get("resources") or [])],
    }
    if stat is not None:  # publishing stats from P1 (datasets.csv)
        d.update({"up": to_int(stat.get("uploads")), "am": to_int(stat.get("active_months")),
                  "fu": stat.get("first_upload") or "", "lu": stat.get("last_upload") or "",
                  "ts": to_int(stat.get("timespan_days"))})
    return d


def feed_item(p):
    org = p.get("organization") or {}
    return {"name": p.get("name") or "", "title": p.get("title") or p.get("name") or "",
            "org": org.get("title") or "", "modified": (p.get("metadata_modified") or "")[:19],
            "notes": (p.get("notes") or "")[:NOTES_MAX]}


def build_data(host, base, jsonl_path, fields_path, stats=None):
    """stats: dataset id -> row of P1 datasets.csv (optional)."""
    stats = stats or {}
    fields = read_fields(fields_path)
    orgs = {}
    datasets = {}
    feed = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            pid = p.get("id") or ""
            if pid in datasets:
                continue
            d = slim_dataset(p, fields, stats.get(pid))
            if d["org"]:
                orgs[d["org"]] = (p.get("organization") or {}).get("title") or d["org"]
            datasets[pid] = d
            feed[pid] = feed_item(p)
    rows = [datasets[k] for k in sorted(datasets)]
    org_size = {}
    files = sized = total = 0
    for d in rows:
        for r in d["res"]:
            files += 1
            if r["size"] is not None:
                sized += 1
                total += r["size"]
                key = d["org"] or "_none"
                org_size[key] = org_size.get(key, 0) + r["size"]
    top = sorted(feed.items(), key=lambda kv: (kv[1]["modified"], kv[0]), reverse=True)[:FEED_MAX]
    return {
        "host": host,
        "base": base,
        "as_of": max((d["modified"] for d in rows), default=""),
        "orgs": orgs,
        "formats": sorted({r["fmt"] for d in rows for r in d["res"]}),
        "has_fields": any("fields" in r for d in rows for r in d["res"]),
        "has_stats": any("up" in d for d in rows),
        "org_size": org_size,
        "totals": {"files": files, "sized": sized, "bytes": total},
        "datasets": rows,
        "feed": [item for _, item in top],  # not written to the JS file
    }


def js_file(data):
    out = {k: v for k, v in data.items() if k != "feed"}
    return "window.BROWSE=" + embed_json(out) + ";\n"


def human_size(n):
    for unit, div in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= div:
            return "%.1f %s" % (n / div, unit)
    return "%d B" % n


def rfc822(stamp):
    """RFC 822 date for 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD' (UTC); '' when it cannot be read."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return format_datetime(datetime.strptime(stamp, fmt).replace(tzinfo=timezone.utc))
        except ValueError:
            pass
    return ""


def rss(data):
    """RSS 2.0 feed of the most recently modified datasets. Links go to the portal."""
    esc = html.escape
    base = data["base"]
    items = []
    for it in data["feed"]:
        link = "%s/dataset/%s" % (base, quote(it["name"], safe=""))
        date = rfc822(it["modified"])
        desc = (it["org"] + ": " if it["org"] else "") + it["notes"]
        items.append(
            "<item><title>%s</title><link>%s</link><guid isPermaLink=\"false\">%s</guid>%s"
            "<description>%s</description></item>\n"
            % (esc(it["title"]), esc(link), esc(link + "#" + it["modified"]),
               ("<pubDate>%s</pubDate>" % date) if date else "", esc(desc)))
    newest = rfc822(data["feed"][0]["modified"]) if data["feed"] else ""
    return ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<rss version=\"2.0\"><channel>\n"
            "<title>%s - recently updated datasets</title><link>%s</link>\n"
            "<description>The %d datasets of %s with the latest metadata change.</description>\n%s%s</channel></rss>\n"
            % (esc(data["host"]), esc(base), len(data["feed"]), esc(data["host"]),
               ("<lastBuildDate>%s</lastBuildDate>\n" % newest) if newest else "", "".join(items)))


# ------------------------------------------------------------------------ page

CSS = """
.ctl{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;align-items:center}
.ctl input,.ctl select{font:inherit;font-size:.9rem;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);max-width:100%}
.ctl input[type=search]{flex:1 1 220px}.ctl input[type=number]{width:7.5em}
a.ext{color:var(--muted);font-size:.8rem;margin-left:6px;white-space:nowrap}
#list th button{background:none;padding:0;font-weight:600;color:inherit}
#list th button[aria-pressed=true]::after{content:attr(data-dir)}
#list td.tt button{background:none;padding:0;font:inherit;font-weight:600;text-align:left;color:var(--fg)}
#list td.tt button::before{content:"\\25B8 ";color:var(--muted)}#list td.tt button[aria-expanded=true]::before{content:"\\25BE "}
#list tr.dt>td{background:var(--panel)}
.body{padding:4px 0 8px 8px}.body p{margin:4px 0}
.tag{display:inline-block;background:var(--bg);border-radius:4px;padding:0 6px;margin:0 4px 4px 0;font-size:.8rem}
.fl{margin:4px 0 0;padding-left:18px;font-size:.8rem;columns:2 220px}
.m{color:var(--muted)}
.ft{margin:8px 0 16px}.ft .sum{margin:0 0 6px;color:var(--muted);font-size:.85rem}
.ft .r{display:grid;grid-template-columns:5.5em minmax(60px,1fr) auto;gap:8px;align-items:center;font-size:.8rem;margin:2px 0}
.ft .bar2{height:8px;border-radius:0 4px 4px 0;background:var(--h3);min-width:1px}
.ft .v{color:var(--muted);white-space:nowrap}
.pager{display:flex;gap:8px;align-items:center;margin:12px 0}
"""

JS = r"""
(function(){
var B=window.BROWSE,PAGE=50;
var S={q:"",org:"",fmt:"",fld:"",upd:"",up:"",am:"",yr:"",sort:"modified",dir:-1,page:0};
function $(id){return document.getElementById(id);}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined&&text!==null)e.textContent=text;return e;}
function link(href,text,cls){var a=el("a",cls||null,text);if(/^https?:\/\//.test(href))a.href=href;return a;}
function opt(sel,v,t){var o=el("option",null,t);o.value=v;sel.appendChild(o);}
function fmtSize(n){if(n===null||n===undefined)return "";if(n<1024)return n+" B";if(n<1048576)return (n/1024).toFixed(1)+" KB";if(n<1073741824)return (n/1048576).toFixed(1)+" MB";return (n/1073741824).toFixed(1)+" GB";}
function orgTitle(o){return o?(B.orgs[o]||o):"(no organization)";}
function cutoff(days){var d=new Date(B.as_of+"T00:00:00Z");d.setUTCDate(d.getUTCDate()-days);return d.toISOString().slice(0,10);}
B.datasets.forEach(function(d){
  d.fmts=[];d.res.forEach(function(r){if(d.fmts.indexOf(r.fmt)<0)d.fmts.push(r.fmt);});
  d.hasf=d.res.some(function(r){return !!r.fields;});
  d.nres=d.res.length;d.orgt=orgTitle(d.org);
  d.hay=(d.title+" "+d.name+" "+d.tags.join(" ")+" "+d.orgt).toLowerCase();
});
B.datasets.forEach(function(d){d.size=d.res.reduce(function(a,r){return a+(r.size||0);},0);});
var UPSAME=B.has_stats&&B.datasets.every(function(d){return d.up===d.nres;});
var COLS=[["title","Title"],["orgt","Organization"],["nres",UPSAME?"Resources (= uploads)":"Res."],["size","Size"]];
if(B.has_stats){
  if(!UPSAME)COLS.push(["up","Uploads"]);
  COLS=COLS.concat([["am","Active months"],["fu","First upload"],["lu","Last upload"],["ts","Timespan (years)"]]);
}
COLS.push(["modified","Modified"]);
var NUM={nres:1,size:1,up:1,am:1,ts:1};
function summarize(list){
  var s={datasets:list.length,files:0,sized:0,bytes:0,fm:{}};
  list.forEach(function(d){d.res.forEach(function(r){
    s.files++;var f=s.fm[r.fmt]||(s.fm[r.fmt]={n:0,b:0});f.n++;
    if(r.size!==null){s.sized++;s.bytes+=r.size;f.b+=r.size;}
  });});
  return s;
}
function typesPanel(box,s){
  box.textContent="";
  var pct=s.files?Math.round(1000*s.sized/s.files)/10:0;
  box.appendChild(el("p","sum",s.datasets.toLocaleString("en-US")+" datasets, "+s.files.toLocaleString("en-US")+" files, "+fmtSize(s.bytes)+" in total (size known for "+s.sized.toLocaleString("en-US")+" files, "+pct+"%). File types by number of files:"));
  var names=Object.keys(s.fm).sort(function(a,b){return s.fm[b].n-s.fm[a].n||(a<b?-1:1);});
  var top=names.slice(0,8),rest=names.slice(8),other={n:0,b:0};
  rest.forEach(function(k){other.n+=s.fm[k].n;other.b+=s.fm[k].b;});
  var rows=top.map(function(k){return [k,s.fm[k]];});
  if(rest.length)rows.push(["Other ("+rest.length+")",other]);
  rows.forEach(function(r){
    var share=s.files?100*r[1].n/s.files:0;
    var row=el("div","r");
    row.title=r[0]+": "+r[1].n.toLocaleString("en-US")+" files ("+share.toFixed(1)+"%), "+fmtSize(r[1].b)+" where the size is known";
    row.appendChild(el("span",null,r[0]));
    var tr=el("span"),bar=el("div","bar2");bar.style.width=Math.max(share,0.3)+"%";tr.appendChild(bar);row.appendChild(tr);
    row.appendChild(el("span","v",share.toFixed(1)+"% \u00b7 "+r[1].n.toLocaleString("en-US")+" files \u00b7 "+fmtSize(r[1].b)));
    box.appendChild(row);
  });
}
if($("gtypes"))typesPanel($("gtypes"),summarize(B.datasets));
function filtered(){
  var words=S.q.toLowerCase().split(/\s+/).filter(Boolean);
  var since=S.upd?cutoff(+S.upd):"",up=+S.up||0,am=+S.am||0,ts=(+S.yr||0)*365.25;
  var out=B.datasets.filter(function(d){
    if(S.org!==""&&d.org!==(S.org==="_none"?"":S.org))return false;
    if(S.fmt&&d.fmts.indexOf(S.fmt)<0)return false;
    if(S.fld==="yes"&&!d.hasf)return false;
    if(since&&d.modified<since)return false;
    if(B.has_stats&&((!UPSAME&&d.up<up)||d.am<am||d.ts<ts))return false;
    return words.every(function(w){return d.hay.indexOf(w)>=0;});
  });
  var k=S.sort,dir=S.dir;
  return out.sort(function(a,b){
    var x=a[k],y=b[k],c=NUM[k]?x-y:(x<y?-1:x>y?1:0);
    if(!c&&k!=="modified"){c=a.modified<b.modified?-1:a.modified>b.modified?1:0;}
    return c*dir||(a.name<b.name?-1:1);
  });
}
function resTable(d){
  var t=el("table"),h=el("tr"),cols=["Resource","Format","Size","Created"];
  if(B.has_fields)cols.push("Fields");
  cols.forEach(function(c){h.appendChild(el("th",null,c));});
  t.appendChild(h);
  d.res.forEach(function(r){
    var tr=el("tr");
    tr.appendChild(el("td",null,r.name));tr.appendChild(el("td",null,r.fmt));
    tr.appendChild(el("td","n",fmtSize(r.size)));tr.appendChild(el("td",null,r.created));
    if(B.has_fields){
      var td=el("td");
      if(r.fields){
        var dt=el("details"),sm=el("summary",null,r.fields.length+" fields"+(r.total!==null&&r.total!==undefined?", "+r.total+" rows":""));
        dt.appendChild(sm);var ul=el("ul","fl");
        r.fields.forEach(function(f){ul.appendChild(el("li",null,f[0]+" \u2014 "+f[1]));});
        dt.appendChild(ul);td.appendChild(dt);
      }
      tr.appendChild(td);
    }
    t.appendChild(tr);
  });
  var w=el("div","scroll");w.appendChild(t);return w;
}
function detail(d){
  var tr=el("tr","dt"),td=el("td");td.colSpan=COLS.length;
  var b=el("div","body");
  if(d.notes)b.appendChild(el("p",null,d.notes));
  if(d.license)b.appendChild(el("p","m","License: "+d.license));
  b.appendChild(el("p","m","Created "+d.created+", modified "+d.modified));
  if(d.tags.length){var tp=el("p");d.tags.forEach(function(t){tp.appendChild(el("span","tag",t));});b.appendChild(tp);}
  if(d.res.length)b.appendChild(resTable(d));
  var p=el("p");p.appendChild(link(B.base+"/dataset/"+encodeURIComponent(d.name),"Open on "+B.host+" \u2197","ext"));
  b.appendChild(p);
  td.appendChild(b);tr.appendChild(td);return tr;
}
function cell(tr,cls,text){tr.appendChild(el("td",cls,text));}
function row(d,tb){
  var tr=el("tr"),td=el("td","tt"),btn=el("button",null,d.title);
  btn.type="button";btn.setAttribute("aria-expanded","false");
  var dt=null;
  btn.addEventListener("click",function(){
    if(dt){dt.remove();dt=null;btn.setAttribute("aria-expanded","false");return;}
    dt=detail(d);tr.after(dt);btn.setAttribute("aria-expanded","true");
  });
  td.appendChild(btn);tr.appendChild(td);
  var o=el("td"),a=el("a",null,d.orgt);a.href="#org="+encodeURIComponent(d.org||"_none");o.appendChild(a);tr.appendChild(o);
  cell(tr,"n",d.nres);cell(tr,"n",d.size?fmtSize(d.size):"");
  if(B.has_stats){if(!UPSAME)cell(tr,"n",d.up);cell(tr,"n",d.am);cell(tr,null,d.fu);cell(tr,null,d.lu);cell(tr,"n",(d.ts/365.25).toFixed(1));}
  cell(tr,null,d.modified);
  tb.appendChild(tr);
}
function head(){
  var th=el("thead"),h=el("tr");
  COLS.forEach(function(c){
    var t=el("th",NUM[c[0]]?"n":null),b=el("button",null,c[1]);b.type="button";
    b.setAttribute("aria-pressed",S.sort===c[0]?"true":"false");b.setAttribute("data-dir",S.dir>0?" \u2191":" \u2193");
    b.addEventListener("click",function(){
      if(S.sort===c[0])S.dir=-S.dir;else{S.sort=c[0];S.dir=(c[0]==="title"||c[0]==="orgt"||c[0]==="fu")?1:-1;}
      S.page=0;render();
    });
    t.appendChild(b);h.appendChild(t);
  });
  th.appendChild(h);return th;
}
function render(){
  var list=filtered(),pages=Math.max(1,Math.ceil(list.length/PAGE));
  if(S.page>=pages)S.page=pages-1;
  typesPanel($("sel"),summarize(list));
  $("count").textContent=list.length.toLocaleString("en-US")+" of "+B.datasets.length.toLocaleString("en-US")+" datasets";
  var box=$("list");box.textContent="";
  if(!list.length){box.appendChild(el("p","sub","No dataset matches."));}
  else{
    var t=el("table");t.appendChild(head());var tb=el("tbody");
    list.slice(S.page*PAGE,(S.page+1)*PAGE).forEach(function(d){row(d,tb);});
    t.appendChild(tb);var w=el("div","scroll");w.appendChild(t);box.appendChild(w);
  }
  $("pinfo").textContent="Page "+(S.page+1)+" of "+pages;
  $("prev").disabled=S.page===0;$("next").disabled=S.page>=pages-1;
  ["q","org","fmt","fld","upd","up","am","yr"].forEach(function(k){if($(k)&&$(k).value!==S[k])$(k).value=S[k];});
}
function bind(id,key){var e=$(id);if(e)e.addEventListener("input",function(ev){S[key]=ev.target.value;S.page=0;render();});}
var so=$("org");opt(so,"","All organizations");
Object.keys(B.orgs).sort(function(a,b){return B.orgs[a].localeCompare(B.orgs[b]);}).forEach(function(k){opt(so,k,B.orgs[k]);});
if(B.datasets.some(function(d){return d.org==="";}))opt(so,"_none","(no organization)");
var sf=$("fmt");opt(sf,"","All formats");B.formats.forEach(function(f){opt(sf,f,f);});
var su=$("upd");opt(su,"","Modified: any time");opt(su,"7","Modified: last 7 days");opt(su,"30","Modified: last 30 days");opt(su,"365","Modified: last year");
if(B.has_fields){var sl=$("fld");sl.hidden=false;opt(sl,"","Fields: any");opt(sl,"yes","Fields: known");}
if(B.has_stats){$("nums").hidden=false;if(UPSAME)$("up").hidden=true;}
["q","org","fmt","fld","upd","up","am","yr"].forEach(function(k){bind(k,k);});
$("prev").addEventListener("click",function(){S.page--;render();});
$("next").addEventListener("click",function(){S.page++;render();});
$("reset").addEventListener("click",function(){S.q=S.org=S.fmt=S.fld=S.upd=S.up=S.am=S.yr="";S.sort="modified";S.dir=-1;S.page=0;render();});
function goOrg(v){
  if(v!=="_none"&&!Object.prototype.hasOwnProperty.call(B.orgs,v))return false;
  S.org=v;S.page=0;render();return true;
}
document.addEventListener("click",function(ev){
  var a=ev.target.closest&&ev.target.closest('a[href^="#org="]');
  if(!a)return;
  var v;try{v=decodeURIComponent(a.getAttribute("href").slice(5));}catch(e){return;}
  if(goOrg(v)){ev.preventDefault();$("datasets").scrollIntoView();}
});
var m=/^#org=(.*)$/.exec(location.hash);
if(m){try{goOrg(decodeURIComponent(m[1]));}catch(e){}}
render();
})();
"""


def section(host):
    """HTML of the browser section: the controls and the empty list."""
    feed = "%s.rss.xml" % html.escape(host, quote=True)
    return (
        "<h2 id=\"datasets\">Datasets</h2>\n"
        "<p class=\"sub\">All datasets of this portal. Uploads are resources, counted by creation date. "
        "Click a column title to sort, a dataset to open it, an organization to filter. "
        "<a href=\"%s\">RSS: recently updated</a>. <span id=\"count\"></span></p>\n"
        "<div class=\"ctl\">"
        "<input id=\"q\" type=\"search\" placeholder=\"Search title, name, tags, organization\" aria-label=\"Search\">"
        "<select id=\"org\" aria-label=\"Organization\"></select>"
        "<select id=\"fmt\" aria-label=\"Format\"></select>"
        "<select id=\"upd\" aria-label=\"Modified\"></select>"
        "<select id=\"fld\" aria-label=\"Fields\" hidden></select>"
        "<span id=\"nums\" hidden>"
        "<input id=\"up\" type=\"number\" min=\"0\" placeholder=\"Min uploads\" aria-label=\"Minimum uploads\"> "
        "<input id=\"am\" type=\"number\" min=\"0\" placeholder=\"Min active months\" aria-label=\"Minimum active months\"> "
        "<input id=\"yr\" type=\"number\" min=\"0\" step=\"0.5\" placeholder=\"Min years\" aria-label=\"Minimum timespan in years\">"
        "</span>"
        "<button id=\"reset\" type=\"button\">Reset</button></div>\n"
        "<div id=\"sel\" class=\"ft\"></div>\n"
        "<div id=\"list\"></div>\n"
        "<div class=\"pager\"><button id=\"prev\">Previous</button><button id=\"next\">Next</button>"
        "<span class=\"sub\" id=\"pinfo\"></span></div>\n" % feed)


def script_tag(host):
    return "<script src=\"%s-datasets.js\"></script>\n" % html.escape(host, quote=True)
