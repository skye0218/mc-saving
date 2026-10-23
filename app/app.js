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
  var currentPlan = null; // 最近一次算出的方案，供下单使用

  // —— 下单跳转目标（按需替换）——
  // 麦当劳官方小程序 AppID（金拱门(中国)有限公司），正式跳转前请替换为真实 AppID，
  // 并在「微信公众平台 → 开发 → 开发管理 → 配置」把官方 AppID 加入互相调用的白名单。
  var MCD_OFFICIAL_APPID = "wxMCD_OFFICIAL_APPID";
  // 官方小程序「点餐/下单确认」页面路径（默认首页，按官方实际路径替换）。
  var MCD_ORDER_PATH = "pages/index/index";
  // 可选：由后端生成的微信 URL Scheme（正式环境用，自动拉起小程序）。留空则走提示兜底。
  var MCD_URL_SCHEME = "";

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
    currentPlan = plan;
    showResult(renderPlan(plan));
    showOrder(plan);
  });

  // —— 下单相关 ——
  function cartBase(plan) {
    var b = 0;
    for (var code in plan.cart) b += menu[code].price * plan.cart[code];
    return b;
  }

  function buildOrderInfo(plan) {
    var items = M.planLines(plan, menu).map(function (l) {
      return { name: l.name, qty: l.qty, price: l.price, gift: !!l.gift };
    });
    var used = (plan.usedCoupons || []).map(function (id) {
      return couponMap[id] ? couponMap[id].desc : id;
    });
    var base = cartBase(plan);
    return {
      items: items, total: plan.total, base: base,
      saved: M.round2(base - plan.total), used: used
    };
  }

  function showOrder(plan) {
    var info = buildOrderInfo(plan);
    var rows = info.items.map(function (it) {
      return '<div class="o-line"><span>' + it.name +
        (it.gift ? "（赠）" : "") + (it.qty > 1 ? " ×" + it.qty : "") +
        '</span><span class="price">' + (it.gift ? "免费" : "¥" + it.price.toFixed(2)) + "</span></div>";
    }).join("");
    var used = info.used.length ? info.used.join("、") : "无";
    document.getElementById("order-summary").innerHTML =
      '<div class="o-lines">' + rows + "</div>" +
      '<div class="o-total">应付 <b>¥' + info.total.toFixed(2) + "</b>　直购 ¥" +
      info.base.toFixed(2) + "　立省 ¥" + info.saved.toFixed(2) + "</div>" +
      '<div class="o-coupons">已用券：' + used + "</div>";
    document.getElementById("order-panel").classList.remove("hidden");
    document.getElementById("order-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  var currentOrderText = "";
  function formatOrderText(info) {
    var lines = info.items.map(function (it) {
      return "· " + it.name + (it.qty > 1 ? " ×" + it.qty : "") +
        (it.gift ? "（赠品）" : " ¥" + it.price.toFixed(2));
    });
    return "【Mc. Saving 最优下单清单】\n" + lines.join("\n") +
      "\n应付：¥" + info.total.toFixed(2) + "（直购 ¥" + info.base.toFixed(2) +
      "，省 ¥" + info.saved.toFixed(2) + "）\n已用券：" +
      (info.used.length ? info.used.join("、") : "无") +
      "\n请到麦当劳官方小程序按此清单点单并使用对应券。";
  }

  function copyText(t) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(t); return true;
      }
    } catch (e) {}
    try {
      var ta = document.createElement("textarea");
      ta.value = t; ta.style.position = "fixed"; ta.style.left = "-9999px";
      document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta); return true;
    } catch (e) { return false; }
  }

  function closeModal() { document.getElementById("order-modal").classList.add("hidden"); }

  function openOrderModal() {
    if (!currentPlan) return;
    var info = buildOrderInfo(currentPlan);
    currentOrderText = formatOrderText(info);
    var linesHtml = info.items.map(function (it) {
      return "<div>" + it.name + (it.qty > 1 ? " ×" + it.qty : "") +
        (it.gift ? "（赠品）" : " ¥" + it.price.toFixed(2)) + "</div>";
    }).join("");
    document.getElementById("modal-body").innerHTML =
      '<div class="m-order">' + linesHtml + "</div>" +
      '<div class="m-total">应付 <b>¥' + info.total.toFixed(2) + "</b> · 省 ¥" +
      info.saved.toFixed(2) + "</div>" +
      '<div class="m-note">已自动复制清单。跳转后按此点单，并使用上方算好的券。</div>' +
      '<div class="m-meta">官方小程序 AppID：<code>' + MCD_OFFICIAL_APPID +
      "</code><br>下单页路径：<code>" + MCD_ORDER_PATH + "</code></div>";
    copyText(currentOrderText);
    document.getElementById("order-modal").classList.remove("hidden");
  }

  function jumpToOfficial() {
    if (MCD_URL_SCHEME) { window.location.href = MCD_URL_SCHEME; return; }
    var inWeChat = /MicroMessenger/i.test(navigator.userAgent);
    alert(inWeChat
      ? "即将打开麦当劳官方小程序（需配置签名 URL Scheme）。\n当前为演示环境：请在微信搜索『麦当劳』小程序，按清单点单。"
      : "请先用手机微信打开本页，再点「打开小程序」即可跳转；或直接微信搜索『麦当劳』小程序按清单点单。");
  }

  document.getElementById("btn-order").addEventListener("click", openOrderModal);
  document.getElementById("modal-open").addEventListener("click", jumpToOfficial);
  document.getElementById("modal-copy").addEventListener("click", function () {
    alert(copyText(currentOrderText) ? "已复制下单清单" : "复制失败，请手动记录");
  });
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("order-modal").addEventListener("click", function (e) {
    if (e.target === this) closeModal();
  });

})();
