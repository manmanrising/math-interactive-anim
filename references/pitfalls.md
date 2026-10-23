# 坑与解法

全部是实际踩过、导致过「交付后用户打不开」的问题。遇到异常先查这里。

---

## 一、白屏 / 点击没有任何反应

这是最高频的故障，按概率排序排查：

### 1. 引了外部 CDN（最常见）

```html
<!-- 致命写法：用户双击 file:// 打开时会被拦，页面卡在加载中 -->
<script src="https://www.geogebra.org/apps/deployggb.js"></script>
```

`file://` 协议下外部脚本容易被浏览器安全策略拦截，表现为：页面结构出来了，但画布空白、按钮全部失灵。

**解法**：一切自己画。SVG 是浏览器原生能力，不需要任何库。字体用系统字体栈。公式用 HTML 的 `<sup>` `<sub>`，不要引 MathJax。

**自检**：`scripts/check_anim.py` 会直接报错。

### 2. 同步加载阻塞整页解析

```html
<!-- 错误：放在 head 里同步加载，网络慢时整页解析停在这里 -->
<script src="xxx.js"></script>
```

外部脚本一旦挂起，后面所有内联脚本都不会执行，页面看起来就是「一片静态 HTML，点啥都没反应」。

**解法**：如确需外部脚本，必须动态异步加载并带失败兜底。

```js
var s = document.createElement('script');
s.src = '...';
s.onload = function(){ /* 初始化 */ };
s.onerror = function(){ /* 显示明确错误提示，不要静默 */ };
document.head.appendChild(s);
```

### 3. 空引用中断整个脚本

```js
// HTML 里没有这个节点 → null → TypeError → 后续所有代码不执行
document.getElementById('pUnit').textContent = '秒';
```

JS 是顺序执行的，一处抛错后面全废。页面表现同样是「控件全部没反应」，而且**不报错给用户看**。

**解法**：所有 DOM 取值走容错辅助函数。

```js
function setText(id, txt){ var n = document.getElementById(id); if(n) n.textContent = txt; }
function setHTML(id, html){ var n = document.getElementById(id); if(n) n.innerHTML = html; }
```

模板的 C 引擎区已经这样实现。若自己新加节点，务必同样处理。

---

## 二、图形比例失真

**现象**：抛物线看着很扁、正方形变成长方形、圆变成椭圆。

**原因**：画布宽高比（如 920:520 ≈ 1.77）与数学坐标范围比例（如 7.4:5.3 ≈ 1.40）不一致，导致 x、y 单位长度不同。

**解法**：映射时对 x、y 使用**同一个缩放系数**，差值部分居中留白。

```js
var SCALE_X = USE_W / RANGE_X;
var SCALE_Y = USE_H / RANGE_Y;
if (V.uniform) { SCALE_X = SCALE_Y = Math.min(SCALE_X, SCALE_Y); }
var OFF_X = V.padl + (USE_W - RANGE_X * SCALE_X) / 2;
var OFF_Y = V.padt + (USE_H - RANGE_Y * SCALE_Y) / 2;
```

**取 `Math.min` 而不是 `Math.max`**：用较小者保证图形完整装在画布内，用较大者会溢出被裁掉。

**注意**：一维数轴题不需要 `uniform`，因为它只有一个维度。

---

## 三、SVG 绘制细节

### 标签与刻度重复

定点 A 若在 −12，而刻度正好也标 −12，就会在轴上下各出现一个 −12，看着很乱。

**解法**：画刻度时跳过定点所在位置，把定点的数值合并进标签：`A(−12)`。

### 文字被线条穿过

动点的竖虚线会穿过标签文字。

**解法**：给文字加白色描边，先描边后填充。

```js
{ 'paint-order':'stroke', stroke:'#fff', 'stroke-width':3.5, 'stroke-linejoin':'round' }
```

### 中文负号

ASCII 的 `-` 又短又靠上，与 `+`、`−` 混排时明显不齐。

**解法**：显示用 `−`（U+2212），代码里的运算仍用 ASCII `-`。

```js
function fx(n){ return (n < 0 ? '−' : '') + Math.abs(n).toFixed(2); }
```

### 两点重合时看不清

两个动点画在同一侧，重合时后画的盖住先画的。

**解法**：一个画在轴上方、一个画在轴下方，各带一条虚竖线投到轴上。

---

## 四、GeoGebra 路线（仅在确需时使用）

GeoGebra 能提供真正的自由点拖动和复杂轨迹，但代价是依赖 CDN，且有若干 API 陷阱。**纯 SVG 能解决的就不要上 GeoGebra。**

若确需使用，以下都是实测踩过的：

| 问题 | 错误写法 | 正确写法 |
|---|---|---|
| 两点距离 | `Length(B, M)` | `Distance(B, M)` |
| 视图范围 | `ZoomIn(-7,-1.5,10,9.5)` | `api.setCoordSystem(-7, 10, -1.5, 9.5)` |
| 条件分段 | 多层 `If` 嵌套易出错 | 尽量改用 `Segment` 参数化，或干脆换纯 SVG |

`Length()` 只接受线段/向量对象，传两个点会返回未定义，进而导致后续依赖它的表达式全部报错（典型症状：弹出「未定义变量 xxx」）。

`evalCommand` 是逐条执行的，任何一条失败不会中断其余命令，所以要**收集失败列表**并显示出来，否则错误会被静默吞掉。

```js
commands.forEach(function(c){
  try { api.evalCommand(c); } catch(e){ fail.push(c); }
});
```

---

## 五、浏览器自动化实测

### 点击打不中

按屏幕坐标点击，页面上下一滚动就偏了；图形里的点更难，需要精确到像素。

**解法**：优先用 DOM 节点点击，不要用坐标。

1. 取可见 DOM 快照，拿到节点的 `node_id`
2. 用 `node_id` 精确点击

比坐标法稳得多，尤其适合点按钮、拖滑块。

### 本地服务无法访问

`python -m http.server` 起在某个端口后访问不到，先确认：

- 端口是否已被占用（换一个端口试）
- 服务是否真的启动成功（看后台任务有没有输出）

经验值：**8899 在本环境验证稳定可用**，8901 曾出现连不上。

### 拖拽图形内的点常常失败

自动化拖拽画布内的 SVG 点，因命中判定严格经常抓空。这不是页面缺陷。

**解法**：不要靠自动化验证「拖动」这个动作，改为**直接点跳转按钮**再核对读数——同样能证明公式正确，而且更可靠。拖拽留给用户手动操作。

---

## 六、交付前检查清单

- [ ] `check_anim.py` 全绿，退出码 0
- [ ] 浏览器打开截图，图形比例正常、标签无重叠
- [ ] 点 2~3 个跳转按钮，读数与手算一致
- [ ] 后台服务已关闭
- [ ] 文字版解答已附上（用户可能只看文字）
- [ ] `present_files` 已交付 HTML
