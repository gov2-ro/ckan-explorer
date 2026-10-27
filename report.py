"""
Build a static HTML report per portal and an index page from P1 stats.

Usage:
    python report.py                 # every data/*/stats/ with summary.json
    python report.py --out site
    python report.py --data data --out site

Reads <data>/<host>/stats/{orgs.csv,org-monthly.csv,datasets.csv,summary.json}.
Writes (overwriting) <out>/index.html and <out>/<host>.html.
Each page is one self-contained file (inline CSS and JavaScript, no external
resources). The same input gives the same bytes: the clock is never used.
Spec: docs/specs/P2-report.md. Standard library only.
"""
import argparse
import csv
import glob
import html
import json
import os
import sys

# host -> base URL of the portal (default: https://<host>)
PORTAL_BASE = {
    "data.gov.md": "https://data.gov.md/ckan",
}

# host -> note shown in the page header
PORTAL_NOTES = {
    "data.humdata.org": (
        "On this portal, `created` dates are probably reset when a file is replaced. "
        "Upload counts can be too low for old data and too high for recent data."
    ),
}

NO_ORG_NAME = "_none"
TOP_N = 50
TABLE_N = 25


# ---------------------------------------------------------------- data helpers

def portal_base(host):
    return PORTAL_BASE.get(host, "https://" + host).rstrip("/")


def month_label(idx):
    return "%04d-%02d" % (idx // 12, idx % 12 + 1)


def window_months(as_of, n):
    """The n calendar months that end with the as-of month (inclusive), oldest first."""
    end = int(as_of[:4]) * 12 + int(as_of[5:7]) - 1
    return [month_label(i) for i in range(end - n + 1, end + 1)]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_portal(stats_dir):
    with open(os.path.join(stats_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    return {
        "summary": summary,
        "orgs": read_csv(os.path.join(stats_dir, "orgs.csv")),
        "monthly": read_csv(os.path.join(stats_dir, "org-monthly.csv")),
        "datasets": read_csv(os.path.join(stats_dir, "datasets.csv")),
    }


def view_columns(as_of, orgs):
    """Column keys per view. 'all' = calendar years, others = months."""
    firsts = [o["first_upload"][:4] for o in orgs if o["first_upload"]]
    as_of_year = int(as_of[:4])
    first_year = min([int(y) for y in firsts] + [as_of_year])
    return {
        "all": [str(y) for y in range(first_year, as_of_year + 1)],
        "y5": window_months(as_of, 60),
        "m12": window_months(as_of, 12),
    }


def col_key(view, month):
    return month[:4] if view == "all" else month


def select_rows(view_cols, orgs, monthly):
    """Per view: indexes (into orgs) of the union of the top 50 by window uploads and
    the top 50 by datasets. Orgs with 0 uploads in the window are left out."""
    result = {}
    for view, cols in view_cols.items():
        colset = set(cols)
        win = {}
        for r in monthly:
            if col_key(view, r["month"]) in colset:
                win[r["org_name"]] = win.get(r["org_name"], 0) + to_int(r["uploads"])
        live = [i for i, o in enumerate(orgs) if win.get(o["org_name"], 0) > 0]
        by_up = sorted(live, key=lambda i: (-win[orgs[i]["org_name"]], orgs[i]["org_name"]))[:TOP_N]
        by_ds = sorted(live, key=lambda i: (-to_int(orgs[i]["datasets"]), orgs[i]["org_name"]))[:TOP_N]
        result[view] = sorted(set(by_up) | set(by_ds))
    return result


def top_tables(datasets, org_titles):
    def row(d):
        span = to_int(d["timespan_days"])
        return [d["name"], d["title"], org_titles.get(d["org_name"], d["org_name"]),
                to_int(d["uploads"]), to_int(d["active_months"]),
                d["first_upload"], d["last_upload"], span]
    live = [d for d in datasets if to_int(d["uploads"]) > 0]
    keys = {
        "span": lambda d: (-to_int(d["timespan_days"]), -to_int(d["uploads"]), d["id"]),
        "months": lambda d: (-to_int(d["active_months"]), -to_int(d["uploads"]), d["id"]),
        "uploads": lambda d: (-to_int(d["uploads"]), -to_int(d["active_months"]), d["id"]),
    }
    return {k: [row(d) for d in sorted(live, key=f)[:TABLE_N]] for k, f in keys.items()}


def build_data(host, portal):
    s = portal["summary"]
    orgs = portal["orgs"]
    as_of = s["as_of"]
    cols = view_columns(as_of, orgs)
    rows = select_rows(cols, orgs, portal["monthly"])
    chosen = sorted(set(i for v in rows.values() for i in v))
    pos = {orgs[i]["org_name"]: n for n, i in enumerate(chosen)}
    cells = {n: [] for n in range(len(chosen))}
    for r in portal["monthly"]:
        n = pos.get(r["org_name"])
        if n is not None:
            cells[n].append([r["month"], to_int(r["uploads"]), to_int(r["updates"]), to_int(r["datasets"])])
    org_out = []
    for n, i in enumerate(chosen):
        o = orgs[i]
        org_out.append({"n": o["org_name"], "t": o["org_title"], "d": to_int(o["datasets"]),
                        "lu": o["last_upload"], "m": cells[n]})
    remap = {i: n for n, i in enumerate(chosen)}
    org_titles = {o["org_name"]: o["org_title"] for o in orgs}
    return {
        "host": host,
        "base": portal_base(host),
        "asof": as_of,
        "views": {v: {"cols": cols[v], "rows": [remap[i] for i in rows[v]]} for v in cols},
        "orgs": org_out,
        "tables": top_tables(portal["datasets"], org_titles),
    }


# ---------------------------------------------------------------- HTML output

def embed_json(obj):
    """JSON for a <script type="application/json"> element; '<' is escaped."""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


CSS = """
:root{--bg:#fff;--fg:#1d1d1b;--muted:#5d5d58;--line:#d9d8d3;--panel:#f6f5f2;--link:#1c5cab;
--h0:#fff;--h1:#cde2fb;--h2:#86b6ef;--h3:#3987e5;--h4:#0d366b;--btn:#eceae5;--btn-on:#1c5cab;--btn-on-fg:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#1b1b19;--fg:#ecebe6;--muted:#a3a29b;--line:#3a3a36;--panel:#242422;--link:#86b6ef;
--h0:#1b1b19;--h1:#104281;--h2:#1c5cab;--h3:#3987e5;--h4:#b7d3f6;--btn:#2d2d2a;--btn-on:#86b6ef;--btn-on-fg:#10151c}}
*{box-sizing:border-box}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto}
h1{font-size:1.4rem;margin:0 0 4px}h2{font-size:1.15rem;margin:28px 0 8px}
a{color:var(--link)}
.sub{color:var(--muted);margin:0 0 12px}
.counts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.counts div{background:var(--panel);border-radius:6px;padding:6px 10px;min-width:96px}
.counts b{display:block;font-size:1.05rem}.counts span{color:var(--muted);font-size:.8rem}
.note{border-left:3px solid var(--link);background:var(--panel);padding:8px 12px;margin:12px 0}
.bar{display:flex;flex-wrap:wrap;gap:6px 16px;margin:8px 0}
.grp{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.grp>span{color:var(--muted);font-size:.85rem;margin-right:2px}
button{font:inherit;font-size:.85rem;border:0;border-radius:6px;padding:5px 10px;background:var(--btn);color:var(--fg);cursor:pointer}
button[aria-pressed=true]{background:var(--btn-on);color:var(--btn-on-fg)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%}
th,td{padding:4px 8px;text-align:left;border-bottom:1px solid var(--line);font-size:.85rem}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.heat td.c,.heat th.c{padding:0;width:14px;min-width:14px;height:20px;border:1px solid var(--bg);text-align:center}
.heat.years td.c,.heat.years th.c{width:44px;min-width:44px}
.heat th.c{height:auto;font-weight:400;color:var(--muted);font-size:.7rem}
.heat th.c.v{writing-mode:vertical-rl;padding:4px 0;white-space:nowrap}
.heat td.org{min-width:170px;max-width:260px}
.l0{background:var(--h0)}.l1{background:var(--h1)}.l2{background:var(--h2)}.l3{background:var(--h3)}.l4{background:var(--h4)}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin:8px 0;font-size:.8rem;color:var(--muted)}
.legend i{display:inline-block;width:16px;height:14px;border:1px solid var(--line);vertical-align:-2px;margin-right:4px}
footer{margin-top:32px;color:var(--muted);font-size:.8rem}
"""

JS = r"""
(function(){
var D=JSON.parse(document.getElementById('data').textContent);
var st={view:'all',sort:'uploads',tab:'span'};
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e}
function link(text,href){var a=el('a',null,text);a.setAttribute('href',href);return a}
function fmt(n){return String(n).replace(/\B(?=(\d{3})+(?!\d))/g,',')}
function buttons(id,opts,key,fn){
  var g=document.getElementById(id);g.textContent='';
  opts.forEach(function(o){
    var b=el('button',null,o[1]);b.type='button';b.setAttribute('aria-pressed',st[key]===o[0]?'true':'false');
    b.onclick=function(){st[key]=o[0];fn()};g.appendChild(b)})}
var cache={};
function cellMap(oi,view){
  var k=view+':'+oi;if(cache[k])return cache[k];
  var m={};D.orgs[oi].m.forEach(function(r){
    var key=view==='all'?r[0].slice(0,4):r[0];var c=m[key]||(m[key]=[0,0,0]);
    c[0]+=r[1];c[1]+=r[2];c[2]+=r[3]});
  return cache[k]=m}
function level(v,max){
  if(v<=0)return 0;
  return 1+Math.min(3,Math.floor(4*Math.log(1+v)/Math.log(1+max)))}
function bound(k,max){
  if(k===1)return 1;
  return Math.max(1,Math.ceil(Math.expm1((k-1)/4*Math.log(1+max))))}
function heat(){
  var V=D.views[st.view],cols=V.cols;
  buttons('vbtn',[['all','All years'],['y5','Last 5 years'],['m12','Last 12 months']],'view',heat);
  buttons('sbtn',[['uploads','Uploads in window'],['last','Last upload'],['datasets','Datasets']],'sort',heat);
  var rows=V.rows.map(function(oi){
    var m=cellMap(oi,st.view),tot=0;
    cols.forEach(function(c){if(m[c])tot+=m[c][0]});
    return {oi:oi,m:m,tot:tot}});
  rows.sort(function(a,b){
    var A=D.orgs[a.oi],B=D.orgs[b.oi],d=0;
    if(st.sort==='last')d=A.lu<B.lu?1:A.lu>B.lu?-1:0;
    else if(st.sort==='datasets')d=B.d-A.d;
    else d=b.tot-a.tot;
    if(!d)d=b.tot-a.tot;
    if(!d)d=A.n<B.n?-1:A.n>B.n?1:0;
    return d});
  var max=1;rows.forEach(function(r){cols.forEach(function(c){if(r.m[c]&&r.m[c][0]>max)max=r.m[c][0]})});
  var t=el('table','heat'+(st.view==='all'?' years':''));
  var h=el('tr');h.appendChild(el('th',null,'Organization'));
  h.appendChild(el('th','n','Uploads'));h.appendChild(el('th','n','Datasets'));
  cols.forEach(function(c){h.appendChild(el('th','c'+(st.view==='all'?'':' v'),c))});
  var th=el('thead');th.appendChild(h);t.appendChild(th);
  var tb=el('tbody');
  rows.forEach(function(r){
    var o=D.orgs[r.oi],tr=el('tr'),td=el('td','org');
    if(o.n==='_none')td.textContent=o.t;
    else td.appendChild(link(o.t,D.base+'/organization/'+encodeURIComponent(o.n)));
    tr.appendChild(td);tr.appendChild(el('td','n',fmt(r.tot)));tr.appendChild(el('td','n',fmt(o.d)));
    cols.forEach(function(c){
      var v=r.m[c],u=v?v[0]:0,cell=el('td','c l'+level(u,max));
      if(v)cell.setAttribute('title',o.t+' | '+c+' | uploads: '+v[0]+' | updates: '+v[1]+' | datasets'+(st.view==='all'?' (sum of months)':'')+': '+v[2]);
      tr.appendChild(cell)});
    tb.appendChild(tr)});
  t.appendChild(tb);
  var box=document.getElementById('heat');box.textContent='';box.appendChild(t);
  var lg=document.getElementById('legend');lg.textContent='';
  lg.appendChild(el('span',null,'Uploads per cell (log scale):'));
  for(var k=0;k<=4;k++){
    var s=el('span'),sw=el('i','l'+k);s.appendChild(sw);
    var lo=k?bound(k,max):0,hi=k<4&&k?bound(k+1,max)-1:null,txt;
    if(k===0)txt='0';else if(k===4)txt=lo+(lo<max?'-'+max:'');
    else txt=hi>lo?lo+'-'+hi:String(lo);
    s.appendChild(document.createTextNode(txt));lg.appendChild(s)}
  document.getElementById('hcount').textContent=rows.length+' organizations shown.'}
function tables(){
  buttons('tbtn',[['span','Longest timespan'],['months','Most active months'],['uploads','Most uploads']],'tab',tables);
  var t=el('table'),h=el('tr');
  ['Title','Organization','Uploads','Active months','First upload','Last upload','Timespan (years)'].forEach(function(x,i){
    h.appendChild(el('th',i>1&&i<4?'n':(i===6?'n':''),x))});
  var th=el('thead');th.appendChild(h);t.appendChild(th);var tb=el('tbody');
  D.tables[st.tab].forEach(function(r){
    var tr=el('tr'),td=el('td');
    td.appendChild(link(r[1]||r[0],D.base+'/dataset/'+encodeURIComponent(r[0])));tr.appendChild(td);
    tr.appendChild(el('td',null,r[2]));
    tr.appendChild(el('td','n',fmt(r[3])));tr.appendChild(el('td','n',fmt(r[4])));
    tr.appendChild(el('td',null,r[5]));tr.appendChild(el('td',null,r[6]));
    tr.appendChild(el('td','n',(r[7]/365.25).toFixed(1)));tb.appendChild(tr)});
  t.appendChild(tb);var box=document.getElementById('tbl');box.textContent='';box.appendChild(t)}
heat();tables();
})();
"""


def page(title, body, script=""):
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n<main>\n%s\n</main>\n%s</body>\n</html>\n"
            % (html.escape(title), CSS, body, script))


def fmt_int(n):
    return "{:,}".format(int(n))


def portal_page(host, portal):
    s = portal["summary"]
    data = build_data(host, portal)
    esc = html.escape
    counts = [("Datasets", s["datasets"]), ("Resources", s["resources"]), ("Uploads", s["uploads"]),
              ("Updates", s["updates"]), ("Organizations", s["orgs"]),
              ("Datasets with no organization", s["no_org_datasets"])]
    cnt = "".join("<div><b>%s</b><span>%s</span></div>" % (fmt_int(v), esc(k)) for k, v in counts)
    note = PORTAL_NOTES.get(host)
    note_html = "<p class=\"note\">%s</p>" % esc(note) if note else ""
    body = (
        "<p><a href=\"index.html\">All portals</a></p>\n"
        "<h1><a href=\"%(base)s\">%(host)s</a></h1>\n"
        "<p class=\"sub\">As of %(asof)s</p>\n"
        "<div class=\"counts\">%(cnt)s</div>\n%(note)s\n"
        "<h2>Top organizations</h2>\n"
        "<p class=\"sub\">Each cell shows uploads (resources by creation date) in the period. "
        "Rows: top 50 organizations by uploads in the window plus top 50 by datasets.</p>\n"
        "<div class=\"bar\"><div class=\"grp\"><span>Period</span><span id=\"vbtn\" class=\"grp\"></span></div>"
        "<div class=\"grp\"><span>Sort</span><span id=\"sbtn\" class=\"grp\"></span></div></div>\n"
        "<div id=\"legend\" class=\"legend\"></div>\n"
        "<div id=\"heat\" class=\"scroll\"></div>\n<p class=\"sub\" id=\"hcount\"></p>\n"
        "<h2>Most active datasets</h2>\n"
        "<div class=\"bar\"><div id=\"tbtn\" class=\"grp\"></div></div>\n"
        "<div id=\"tbl\" class=\"scroll\"></div>\n"
        "<footer>Data: P1 stats (orgs.csv, org-monthly.csv, datasets.csv) from %(host)s.</footer>"
    ) % {"base": esc(data["base"], quote=True), "host": esc(host), "asof": esc(s["as_of"]),
         "cnt": cnt, "note": note_html}
    script = ("<script id=\"data\" type=\"application/json\">%s</script>\n<script>%s</script>\n"
              % (embed_json(data), JS))
    return page(host + " - publishing report", body, script)


def index_row(host, portal):
    s = portal["summary"]
    real = [o for o in portal["orgs"] if o["org_name"] != NO_ORG_NAME]
    total = sum(to_int(o["uploads"]) for o in portal["orgs"])
    top10 = sum(sorted((to_int(o["uploads"]) for o in real), reverse=True)[:10])
    return {
        "host": host, "as_of": s["as_of"], "datasets": s["datasets"], "uploads": s["uploads"],
        "orgs": s["orgs"],
        "uploads_12m": sum(to_int(o["uploads_12m"]) for o in portal["orgs"]),
        "orgs_12m": sum(1 for o in real if to_int(o["uploads_12m"]) > 0),
        "top10": (100.0 * top10 / total) if total else 0.0,
    }


def index_page(portals):
    rows = sorted((index_row(h, p) for h, p in portals.items()),
                  key=lambda r: (-r["datasets"], r["host"]))
    esc = html.escape
    head = ["Portal", "As of", "Datasets", "Uploads", "Organizations", "Uploads, last 12 months",
            "Organizations with upload, last 12 months", "Top 10 organizations, share of uploads"]
    th = "".join("<th%s>%s</th>" % ("" if i < 2 else " class=\"n\"", esc(h)) for i, h in enumerate(head))
    tr = ""
    for r in rows:
        tr += ("<tr><td><a href=\"%s.html\">%s</a></td><td>%s</td><td class=\"n\">%s</td><td class=\"n\">%s</td>"
               "<td class=\"n\">%s</td><td class=\"n\">%s</td><td class=\"n\">%s</td><td class=\"n\">%.1f%%</td></tr>\n"
               % (esc(r["host"], quote=True), esc(r["host"]), esc(r["as_of"]), fmt_int(r["datasets"]),
                  fmt_int(r["uploads"]), fmt_int(r["orgs"]), fmt_int(r["uploads_12m"]),
                  fmt_int(r["orgs_12m"]), r["top10"]))
    notes = "".join("<p class=\"note\">%s</p>\n" % esc(h + ": " + PORTAL_NOTES[h])
                    for h in sorted(portals) if h in PORTAL_NOTES)
    body = ("<h1>CKAN portals: who publishes, and when</h1>\n"
            "<p class=\"sub\">Uploads are resources, counted in the month of their creation date. "
            "Organization counts do not include datasets with no organization.</p>\n"
            "<div class=\"scroll\"><table><thead><tr>%s</tr></thead>\n<tbody>\n%s</tbody></table></div>\n"
            "%s"
            % (th, tr, notes))
    return page("CKAN portals - publishing report", body)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser(description="Build static HTML reports from P1 stats.")
    ap.add_argument("--data", default="data", help="directory with <host>/stats/ (default: data)")
    ap.add_argument("--out", default="site", help="output directory (default: site)")
    args = ap.parse_args()
    portals = {}
    for summ in sorted(glob.glob(os.path.join(args.data, "*", "stats", "summary.json"))):
        stats_dir = os.path.dirname(summ)
        host = os.path.basename(os.path.dirname(stats_dir))
        portals[host] = load_portal(stats_dir)
    if not portals:
        sys.exit("No %s/*/stats/summary.json found. Run org-stats.py first." % args.data)
    os.makedirs(args.out, exist_ok=True)
    for host, portal in portals.items():
        text = portal_page(host, portal)
        write(os.path.join(args.out, host + ".html"), text)
        print("%s: %d bytes" % (host, len(text.encode("utf-8"))))
    text = index_page(portals)
    write(os.path.join(args.out, "index.html"), text)
    print("index: %d bytes" % len(text.encode("utf-8")))


if __name__ == "__main__":
    main()
