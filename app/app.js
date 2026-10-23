/* Mc. Saving H5 交互逻辑 */
(function () {
  "use strict";
  var M = window.McSaving;
  var D = window.McSavingData;
  if (!M || !D) { alert("引擎未加载"); return; }

  var menu = M.menuFromJson(D.MEALS);
  var coupons = M.couponsFromJson(D.COUPONS);
  var couponMap = {};
  coupons.forEach(function (c) { couponMap[c.coupon_id] = c; });

  var selected = {}; // code -> true

  // 渲染菜单
  var grid = document.getElementById("menu-grid");
  var currentCat = "all";

  function catOf(it) { return (it.tags && it.tags[0]) || "其他"; }

  function renderCatTabs() {
    var box = document.getElementById("cat-tabs");
    var seen = [];
    D.MEALS.meals.forEach(function (it) {
      var c = catOf(it);
      if (seen.indexOf(c) < 0) seen.push(c);
    });
    var cats = ["all"].concat(seen);
    box.innerHTML = "";
    cats.forEach(function (c) {
      var b = document.createElement("button");
      b.className = "cat" + (c === currentCat ? " active" : "");
      b.textContent = (c === "all" ? "全部" : c);
      b.addEventListener("click", function () {
        currentCat = c;
        renderCatTabs();
        renderMenu();
      });
      box.appendChild(b);
    });
  }

  function renderMenu() {
    grid.innerHTML = "";
    D.MEALS.meals.forEach(function (it) {
      if (currentCat !== "all" && catOf(it) !== currentCat) return;
      var el = document.createElement("div");
      el.className = "item" + (selected[it.code] ? " sel" : "");
      var tags = (it.tags || []).map(function (t) {
        return '<span class="tag">' + t + "</span>";
      }).join("");
      el.innerHTML =
        '<div class="chk"></div>' +
        '<div class="nm">' + it.name + "</div>" +
        '<div class="pr">¥' + Number(it.price).toFixed(2) + "</div>" +
        '<div class="tg">' + tags + "</div>";
      el.addEventListener("click", function () {
        if (selected[it.code]) { delete selected[it.code]; el.classList.remove("sel"); }
        else { selected[it.code] = true; el.classList.add("sel"); }
      });
      grid.appendChild(el);
    });
  }
  renderCatTabs();
  renderMenu();

  // 渲染优惠券
  var cl = document.getElementById("coupon-list");
  var kindName = { item_price: "单品价", percent: "折扣", threshold: "满减", bundle_price: "组合价", free_gift: "赠品" };
  function renderCoupons() {
    cl.innerHTML = "";
    coupons.forEach(function (c) {
      var el = document.createElement("div");
      el.className = "coupon";
      el.innerHTML =
        '<span class="badge">' + (kindName[c.kind] || c.kind) + "</span>" +
        '<span class="cd">' + c.desc + "</span>" +
        (c.stackable ? '<span class="stk">可叠加</span>' : '<span class="stk" style="color:#b06">不可叠加</span>');
      cl.appendChild(el);
    });
  }
  renderCoupons();

  // Tab 切换
  var tabs = document.querySelectorAll(".tab");
  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      tabs.forEach(function (x) { x.classList.remove("active"); });
      t.classList.add("active");
      var tab = t.getAttribute("data-tab");
      document.getElementById("panel-wish").classList.toggle("hidden", tab !== "wish");
      document.getElementById("panel-budget").classList.toggle("hidden", tab !== "budget");
    });
  });

  // 全选/清空
  document.getElementById("btn-all").addEventListener("click", function () {
    D.MEALS.meals.forEach(function (it) {
      if (currentCat === "all" || catOf(it) === currentCat) selected[it.code] = true;
    });
    renderMenu();
  });
  document.getElementById("btn-clear").addEventListener("click", function () {
    D.MEALS.meals.forEach(function (it) {
      if (currentCat === "all" || catOf(it) === currentCat) delete selected[it.code];
    });
    renderMenu();
  });

  // 结果渲染
  var resultPanel = document.getElementById("result-panel");
  var resultEl = document.getElementById("result");
  function showResult(html) {
    resultEl.innerHTML = html;
    resultPanel.classList.remove("hidden");
    resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderPlan(plan) {
    var base = 0;
    for (var code in plan.cart) base += menu[code].price * plan.cart[code];
    var saved = M.round2(base - plan.total);
    var lines = M.planLines(plan, menu).map(function (l) {
      if (l.gift) {
        return '<div class="r-line"><span class="gift">🎁 ' + l.name + ' ×1</span><span class="price">免费</span></div>';
      }
      return '<div class="r-line"><span>' + l.name + ' ×' + l.qty + '</span><span class="price">¥' + l.price.toFixed(2) + '</span></div>';
    }).join("");
    var used = (plan.usedCoupons || []).map(function (id) {
      return couponMap[id] ? couponMap[id].desc : id;
    }).join("、");
    var couponHtml = used ? '<div class="r-coupons">已用券：<b>' + used + "</b></div>" : '<div class="r-coupons">未用到券</div>';
    var explain = renderExplanation(plan, base);
    return (
      '<div class="total-box">' +
        '<div class="lbl">最优应付</div>' +
        '<div class="pay">¥' + plan.total.toFixed(2) + "</div>" +
        '<div class="save">直购 ¥' + base.toFixed(2) + " · 立省 ¥" + saved.toFixed(2) + "</div>" +
      "</div>" +
      lines + couponHtml + explain
    );
  }

  // 把"怎么算出来的"逐步展示出来，让最优方案可解释
  function renderExplanation(plan, base) {
    var steps = plan.steps || [];
    if (!steps.length) {
      return '<div class="r-explain"><div class="ex-title">🧮 计算说明</div>' +
        '<div class="ex-note">本方案未使用优惠券，已直接按菜单原价 ¥' + base.toFixed(2) + ' 结算；' +
        '算法共比较了 ' + (plan.tried || 0) + ' 种券组合，均无更低价。</div></div>';
    }
    var rows = steps.map(function (s) {
      if (s.gift) {
        return '<div class="ex-row gift"><span class="ex-lbl">🎁 ' + s.label + '</span>' +
          '<span class="ex-detail">' + s.detail + '</span></div>';
      }
      return '<div class="ex-row">' +
        '<span class="ex-lbl">' + s.label + '</span>' +
        '<span class="ex-detail">' + s.detail + '</span>' +
        '<span class="ex-flow">¥' + s.before.toFixed(2) + ' → <b>¥' + s.after.toFixed(2) + '</b></span>' +
        '<span class="ex-save">省¥' + s.saved.toFixed(2) + '</span>' +
      '</div>';
    }).join("");
    var note = '算法对 ' + (plan.tried || 0) + ' 种可叠加券组合做了完整枚举，不可叠加券单独比对；' +
      '并按「单品改价 → 组合价 → 折扣 → 满减」顺序结算（赠品只送不扣款），' +
      '最终取应付最低且赠品最多的方案。';
    return '<div class="r-explain">' +
      '<div class="ex-title">🧮 计算说明（一步步怎么算的）</div>' +
      rows +
      '<div class="ex-note">' + note + '</div>' +
    '</div>';
  }

  // 点名最省
  document.getElementById("btn-wish").addEventListener("click", function () {
    var codes = Object.keys(selected);
    if (codes.length === 0) { alert("先勾选至少一样想吃的～"); return; }
    var plan = M.cheapestForWishlist(codes, menu, coupons)[0];
    if (!plan) { alert("没有可计算的项目"); return; }
    showResult(renderPlan(plan));
  });

  // 预算内最值
  document.getElementById("btn-budget").addEventListener("click", function () {
    var b = parseFloat(document.getElementById("budget-input").value);
    if (!(b > 0)) { alert("请输入有效预算"); return; }
    var plans = M.budgetCombos(menu, coupons, b, 3);
    var box = document.getElementById("budget-result");
    if (!plans.length) { box.innerHTML = '<div class="hint">该预算内没有可组的搭配，试试调高预算。</div>'; return; }
    box.innerHTML = plans.map(function (p, i) {
      var names = M.planLines(p, menu).map(function (l) {
        return l.name + (l.gift ? "(赠)" : "");
      }).join(" + ");
      var used = (p.usedCoupons || []).map(function (id) {
        return couponMap[id] ? couponMap[id].desc : id;
      }).join("、");
      return (
        '<div class="bcard">' +
          '<div class="bt">方案 ' + (i + 1) + ' · 实付 ¥' + p.total.toFixed(2) + "</div>" +
          '<div class="blines">' + names + "</div>" +
          '<div class="bsave">省 ¥' + p.saved.toFixed(2) + "　已用：" + (used || "无") + "</div>" +
        "</div>"
      );
    }).join("");
  });
})();
