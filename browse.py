"""
Dataset browser section for the portal pages: reads datasets.jsonl (and fields.jsonl).

Used by report.py; it has no command line of its own.
    build_data(host, base, jsonl_path, fields_path) -> dict
    js_file(data)  -> text of <out>/<host>-datasets.js
    section(host)  -> HTML of the section; CSS and JS are the styles and script

The same input gives the same bytes: the clock is never used.
Spec: docs/specs/P7-dataset-browser.md. Standard library only.
"""
import html
import json
import os

NOTES_MAX = 300
NAME_MAX = 120
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


def slim_dataset(p, fields):
    org = p.get("organization") or {}
    return {
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


def build_data(host, base, jsonl_path, fields_path):
    fields = read_fields(fields_path)
    orgs = {}
    datasets = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            d = slim_dataset(p, fields)
            if d["org"]:
                orgs[d["org"]] = (p.get("organization") or {}).get("title") or d["org"]
            datasets.setdefault(p.get("id") or "", d)
    rows = [datasets[k] for k in sorted(datasets)]
    formats = sorted({r["fmt"] for d in rows for r in d["res"]})
    return {
        "host": host,
        "base": base,
        "as_of": max((d["modified"] for d in rows), default=""),
        "orgs": orgs,
        "formats": formats,
        "has_fields": any("fields" in r for d in rows for r in d["res"]),
        "datasets": rows,
    }


def js_file(data):
    return "window.BROWSE=" + embed_json(data) + ";\n"


# ------------------------------------------------------------------------ page

CSS = """
.ctl{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.ctl input,.ctl select{font:inherit;font-size:.9rem;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);max-width:100%}
.ctl input{flex:1 1 220px}
details.ds{border-bottom:1px solid var(--line);padding:6px 4px}
details.ds>summary{cursor:pointer;display:flex;flex-wrap:wrap;gap:2px 12px;align-items:baseline}
details.ds .t{font-weight:600;flex:1 1 280px}
details.ds .m{color:var(--muted);font-size:.8rem}
.body{padding:8px 0 8px 16px}
.body p{margin:4px 0}.tag{display:inline-block;background:var(--panel);border-radius:4px;padding:0 6px;margin:0 4px 4px 0;font-size:.8rem}
.fl{margin:4px 0 0;padding-left:18px;font-size:.8rem;columns:2 220px}
.pager{display:flex;gap:8px;align-items:center;margin:12px 0}
"""

JS = r"""
(function(){
var B=window.BROWSE,PAGE=50,S={q:"",org:"",fmt:"",fld:"",sort:"modified",page:0};
function $(id){return document.getElementById(id);}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined&&text!==null)e.textContent=text;return e;}
function link(href,text){var a=el("a",null,text);if(/^https?:\/\//.test(href))a.href=href;return a;}
function opt(sel,v,t){var o=el("option",null,t);o.value=v;sel.appendChild(o);}
function fmtSize(n){if(n===null||n===undefined)return "";if(n<1024)return n+" B";if(n<1048576)return (n/1024).toFixed(1)+" KB";if(n<1073741824)return (n/1048576).toFixed(1)+" MB";return (n/1073741824).toFixed(1)+" GB";}
function orgTitle(o){return o?(B.orgs[o]||o):"(no organization)";}
B.datasets.forEach(function(d){
  d.fmts=[];d.res.forEach(function(r){if(d.fmts.indexOf(r.fmt)<0)d.fmts.push(r.fmt);});
  d.hasf=d.res.some(function(r){return !!r.fields;});
  d.hay=(d.title+" "+d.name+" "+d.tags.join(" ")+" "+orgTitle(d.org)).toLowerCase();
});
var sorts={
  modified:function(a,b){return a.modified<b.modified?1:a.modified>b.modified?-1:0;},
  created:function(a,b){return a.created<b.created?1:a.created>b.created?-1:0;},
  resources:function(a,b){return b.res.length-a.res.length;},
  title:function(a,b){return a.title.localeCompare(b.title);}
};
function filtered(){
  var words=S.q.toLowerCase().split(/\s+/).filter(Boolean);
  var out=B.datasets.filter(function(d){
    if(S.org!==""&&d.org!==(S.org==="_none"?"":S.org))return false;
    if(S.fmt&&d.fmts.indexOf(S.fmt)<0)return false;
    if(S.fld==="yes"&&!d.hasf)return false;
    return words.every(function(w){return d.hay.indexOf(w)>=0;});
  });
  return out.sort(sorts[S.sort]);
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
        r.fields.forEach(function(f){ul.appendChild(el("li",null,f[0]+" — "+f[1]));});
        dt.appendChild(ul);td.appendChild(dt);
      }
      tr.appendChild(td);
    }
    t.appendChild(tr);
  });
  var w=el("div","scroll");w.appendChild(t);return w;
}
function fill(det,d){
  var b=el("div","body");
  if(d.notes)b.appendChild(el("p",null,d.notes));
  var p=el("p");p.appendChild(link(B.base+"/dataset/"+encodeURIComponent(d.name),"Open on portal"));
  b.appendChild(p);
  if(d.license)b.appendChild(el("p","m","License: "+d.license));
  b.appendChild(el("p","m","Created "+d.created+", modified "+d.modified));
  if(d.tags.length){var tp=el("p");d.tags.forEach(function(t){tp.appendChild(el("span","tag",t));});b.appendChild(tp);}
  if(d.res.length)b.appendChild(resTable(d));
  det.appendChild(b);
}
function row(d){
  var det=el("details","ds"),sm=el("summary");
  sm.appendChild(el("span","t",d.title));
  sm.appendChild(el("span","m",orgTitle(d.org)));
  sm.appendChild(el("span","m",d.res.length+" res."));
  sm.appendChild(el("span","m",d.fmts.join(", ")));
  sm.appendChild(el("span","m",d.modified));
  det.appendChild(sm);
  det.addEventListener("toggle",function(){if(det.open&&det.children.length===1)fill(det,d);});
  return det;
}
function render(){
  var list=filtered(),pages=Math.max(1,Math.ceil(list.length/PAGE));
  if(S.page>=pages)S.page=pages-1;
  $("count").textContent=list.length.toLocaleString("en-US")+" of "+B.datasets.length.toLocaleString("en-US")+" datasets";
  var box=$("list");box.textContent="";
  if(!list.length)box.appendChild(el("p","sub","No dataset matches."));
  list.slice(S.page*PAGE,(S.page+1)*PAGE).forEach(function(d){box.appendChild(row(d));});
  $("pinfo").textContent="Page "+(S.page+1)+" of "+pages;
  $("prev").disabled=S.page===0;$("next").disabled=S.page>=pages-1;
}
function bind(id,key){$(id).addEventListener("input",function(e){S[key]=e.target.value;S.page=0;render();});}
var so=$("org");opt(so,"","All organizations");
Object.keys(B.orgs).sort(function(a,b){return B.orgs[a].localeCompare(B.orgs[b]);}).forEach(function(k){opt(so,k,B.orgs[k]);});
if(B.datasets.some(function(d){return d.org==="";}))opt(so,"_none","(no organization)");
var sf=$("fmt");opt(sf,"","All formats");B.formats.forEach(function(f){opt(sf,f,f);});
if(B.has_fields){var sl=$("fld");sl.hidden=false;opt(sl,"","Fields: any");opt(sl,"yes","Fields: known");bind("fld","fld");}
bind("q","q");bind("org","org");bind("fmt","fmt");bind("sort","sort");
$("prev").addEventListener("click",function(){S.page--;render();});
$("next").addEventListener("click",function(){S.page++;render();});
render();
})();
"""


def section(host):
    """HTML of the browser section: the controls and the empty list."""
    return (
        "<h2 id=\"datasets\">Datasets</h2>\n"
        "<p class=\"sub\">Search all datasets of this portal. <span id=\"count\"></span></p>\n"
        "<div class=\"ctl\">"
        "<input id=\"q\" type=\"search\" placeholder=\"Search title, name, tags, organization\" aria-label=\"Search\">"
        "<select id=\"org\" aria-label=\"Organization\"></select>"
        "<select id=\"fmt\" aria-label=\"Format\"></select>"
        "<select id=\"fld\" aria-label=\"Fields\" hidden></select>"
        "<select id=\"sort\" aria-label=\"Sort\">"
        "<option value=\"modified\">Sort: last modified</option><option value=\"created\">Sort: created</option>"
        "<option value=\"resources\">Sort: most resources</option><option value=\"title\">Sort: title</option>"
        "</select></div>\n"
        "<div id=\"list\"></div>\n"
        "<div class=\"pager\"><button id=\"prev\">Previous</button><button id=\"next\">Next</button>"
        "<span class=\"sub\" id=\"pinfo\"></span></div>\n")


def script_tag(host):
    return "<script src=\"%s-datasets.js\"></script>\n" % html.escape(host, quote=True)
