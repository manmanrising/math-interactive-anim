#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_anim.py —— 交互动图 HTML 一键自检

用途：生成动图页面后立刻跑一遍，抓出「语法错 / 运行时崩 / 缺 DOM 节点 /
      读数没渲染 / 引了外部 CDN」这几类问题，避免交付后才被用户发现白屏。

用法：
    python check_anim.py <动图.html>

退出码：0 = 全部通过；1 = 存在 ERROR
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# 引擎区必须存在的 DOM 节点（缺任何一个都会导致页面半死）
REQUIRED_IDS = [
    "svg", "slider", "play",
    "layerStatic", "layerDynamic",
    "readoutBox", "jumps",
]

OK, WARN, ERR = "OK", "WARN", "ERROR"
results = []


def add(level, title, detail=""):
    results.append((level, title, detail))


def read_html(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_inline_js(html):
    """取最后一个无 src 的内联 <script>（引擎逻辑所在）"""
    blocks = re.findall(r"<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>", html, re.S)
    return blocks[-1] if blocks else ""


def extract_ids(html):
    return set(re.findall(r'\bid\s*=\s*["\']([A-Za-z_][\w\-]*)["\']', html))


def check_external(html):
    refs = re.findall(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)["\']', html)
    if refs:
        add(ERR, "存在外部资源依赖（file:// 双击打开会白屏）",
            " / ".join(refs[:5]))
    else:
        add(OK, "零外部依赖，可离线双击打开")


def check_ids(html):
    ids = extract_ids(html)
    missing = [i for i in REQUIRED_IDS if i not in ids]
    if missing:
        add(ERR, "缺少引擎必需的 DOM 节点", ", ".join(missing))
    else:
        add(OK, "引擎必需 DOM 节点齐全")
    return ids


def check_js_syntax(js):
    node = shutil.which("node")
    if not node:
        add(WARN, "未找到 node，跳过 JS 语法检查")
        return True
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js)
        tmp = f.name
    try:
        p = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if p.returncode != 0:
            add(ERR, "JS 语法错误", (p.stderr or "").strip()[:600])
            return False
        add(OK, "JS 语法通过")
        return True
    finally:
        os.unlink(tmp)


MOCK_RUNNER = r"""
// ---------- 最小 DOM 模拟 ----------
var EXISTING = __IDS__;
function makeEl(tag){
  var e = {
    tagName: tag, _attrs: {}, children: [], _text: '', _html: '',
    style: {}, className: '', value: '0',
    min: 0, max: 10, step: 0.05, textContent: '', innerHTML: '',
    setAttribute: function(k, v){ this._attrs[k] = v; },
    getAttribute: function(k){ return this._attrs[k]; },
    appendChild: function(c){ this.children.push(c); return c; },
    addEventListener: function(){}, removeEventListener: function(){},
    click: function(){}, focus: function(){},
    querySelector: function(){ return null; }
  };
  Object.defineProperty(e, 'textContent', {
    get: function(){ return this._text; },
    set: function(v){ this._text = String(v); }
  });
  Object.defineProperty(e, 'innerHTML', {
    get: function(){ return this._html; },
    set: function(v){ this._html = String(v); }
  });
  return e;
}
var REG = {};
global.document = {
  getElementById: function(id){
    if (EXISTING.indexOf(id) === -1) return null;   // 模拟真实浏览器：不存在的 id 返回 null
    if (!REG[id]) REG[id] = makeEl('div#' + id);
    return REG[id];
  },
  createElement: function(t){ return makeEl(t); },
  createElementNS: function(ns, t){ return makeEl(t); },
  addEventListener: function(){},
  body: makeEl('body')
};
global.window = global;
global.requestAnimationFrame = function(){ return 0; };
global.cancelAnimationFrame = function(){};

// ---------- 执行页面脚本 ----------
var RUNTIME_ERROR = null;
try {
  __CODE__
} catch (err) {
  RUNTIME_ERROR = (err && err.message ? err.message : String(err));
}

// ---------- 收集结果 ----------
function kid(id){ return (REG[id] && REG[id].children) ? REG[id].children.length : 0; }
function txt(id, n){
  var e = REG[id];
  if (!e || !e.children[n]) return null;
  return e.children[n]._text;
}

var ro = REG['readoutBox'] ? REG['readoutBox'].children : [];
var readouts = [];
for (var i = 0; i < ro.length; i++) {
  var kids = ro[i].children || [];
  readouts.push({
    label: kids[0] ? kids[0]._text : '',
    value: kids[1] ? kids[1]._text : ''
  });
}

var out = {
  runtimeError: RUNTIME_ERROR,
  staticNodes: kid('layerStatic'),
  dynamicNodes: kid('layerDynamic'),
  jumpButtons: kid('jumps'),
  readouts: readouts,
  sliderValue: REG['slider'] ? REG['slider'].value : null,
  title: REG['hTitle'] ? REG['hTitle']._text : null
};
console.log('__RESULT__' + JSON.stringify(out));
"""


def check_runtime(js, ids):
    node = shutil.which("node")
    if not node:
        add(WARN, "未找到 node，跳过运行时检测")
        return None

    runner = (MOCK_RUNNER
              .replace("__IDS__", json.dumps(sorted(ids)))
              .replace("__CODE__", js))

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(runner)
        tmp = f.name
    try:
        p = subprocess.run([node, tmp], capture_output=True, text=True, timeout=30)
        raw = (p.stdout or "") + (p.stderr or "")
        m = re.search(r"__RESULT__(\{.*\})", raw, re.S)
        if not m:
            add(ERR, "运行时检测未返回结果", raw.strip()[:600])
            return None
        data = json.loads(m.group(1))
    except subprocess.TimeoutExpired:
        add(ERR, "运行时检测超时（可能存在死循环）")
        return None
    finally:
        os.unlink(tmp)

    if data.get("runtimeError"):
        add(ERR, "运行时报错（页面会白屏或控件失效）", data["runtimeError"])
        return data

    add(OK, "页面脚本执行无报错")

    sn = data.get("staticNodes") or 0
    dn = data.get("dynamicNodes") or 0
    if sn < 2:
        add(ERR, "静态层几乎没有图形元素", "layerStatic 子节点数 = %d" % sn)
    else:
        add(OK, "静态图形已生成", "%d 个 SVG 元素" % sn)
    if dn < 2:
        add(ERR, "动态层几乎没有元素", "layerDynamic 子节点数 = %d" % dn)
    else:
        add(OK, "动态元素已生成", "%d 个 SVG 元素" % dn)

    rd = data.get("readouts") or []
    if not rd:
        add(WARN, "没有读数卡片（可选）")
    else:
        blank = [r["label"] for r in rd if not r["value"] or r["value"] == "—"]
        if blank:
            add(ERR, "读数未渲染（renderFrame 未返回该 id）", ", ".join(blank))
        else:
            add(OK, "读数全部渲染", " | ".join("%s=%s" % (r["label"], r["value"]) for r in rd))

    return data


def check_math_hooks(js):
    for fn in ("stateAt", "buildStatic", "buildDynamic", "renderFrame"):
        if not re.search(r"function\s+%s\s*\(" % fn, js):
            add(ERR, "缺少约定函数 %s()" % fn)
            return
    add(OK, "四个约定函数齐全（stateAt/buildStatic/buildDynamic/renderFrame）")


def main():
    if len(sys.argv) < 2:
        print("用法: python check_anim.py <动图.html>")
        return 2
    path = sys.argv[1]
    if not os.path.isfile(path):
        print("文件不存在: %s" % path)
        return 2

    html = read_html(path)
    js = extract_inline_js(html)

    print("=" * 62)
    print("自检: %s" % os.path.basename(path))
    print("=" * 62)

    if not js:
        add(ERR, "页面里没有内联 JS")
    else:
        check_external(html)
        ids = check_ids(html)
        ok_syntax = check_js_syntax(js)
        check_math_hooks(js)
        if ok_syntax:
            check_runtime(js, ids)

    errs = [r for r in results if r[0] == ERR]
    warns = [r for r in results if r[0] == WARN]

    for level, title, detail in results:
        mark = {"OK": "  ✅", "WARN": "  ⚠️", "ERROR": "  ❌"}[level]
        print("%s %s" % (mark, title))
        if detail:
            for line in str(detail).splitlines():
                print("       %s" % line)

    print("-" * 62)
    if errs:
        print("结果: 失败（%d 个错误, %d 个警告）—— 修完再交付" % (len(errs), len(warns)))
        return 1
    print("结果: 通过（%d 个警告）—— 可以交付" % len(warns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
