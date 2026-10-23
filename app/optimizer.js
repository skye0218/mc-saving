/*
 * Mc. Saving —— 确定性价格优化器（纯 JS 移植，零依赖）
 * ------------------------------------------------------------
 * 与 Python 版 optimizer.py 行为完全一致：
 *   取数交给 MCP，算术交给代码。同一份输入永远得到同一份输出。
 *
 * 本文件同时兼容：
 *   - 浏览器 <script src> 引入（挂到 window.McSaving）
 *   - Node / 微信小程序 require() 引入（module.exports）
 *
 * 优惠券类型：
 *   item_price   : 单品改价（target 单品 code，fixed 改后单价）
 *   percent      : 折扣（discount 比例 0~1，可设 min_spend 满额门槛）
 *   threshold    : 满减（threshold 门槛，reduce 减免额）
 *   bundle_price : 组合价（从 bundle_items 池任选 min_count 件按 bundle_price 计价）
 *   free_gift    : 赠品（target 为需购买单品，gift 为赠送单品；target 为空表示随单赠）
 */
(function (global, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    global.McSaving = factory();
  }
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this), function () {

  function round2(x) {
    return Math.round((x + 1e-9) * 100) / 100;
  }

  // 生成数组的所有 r 组合
  function combinations(arr, r) {
    var res = [];
    (function helper(start, combo) {
      if (combo.length === r) { res.push(combo.slice()); return; }
      for (var i = start; i < arr.length; i++) {
        combo.push(arr[i]);
        helper(i + 1, combo);
        combo.pop();
      }
    })(0, []);
    return res;
  }

  function _applicable(c, cart, baseTotal) {
    if (c.kind === "item_price") return (cart[c.target] || 0) > 0;
    if (c.kind === "threshold") return baseTotal >= (c.threshold || 0);
    if (c.kind === "bundle_price") {
      var pool = (c.bundle_items || []).filter(function (i) { return (cart[i] || 0) > 0; });
      return pool.length >= c.min_count;
    }
    if (c.kind === "free_gift") {
      return c.target === null || c.target === undefined || (cart[c.target] || 0) > 0;
    }
    if (c.kind === "percent") {
      if (c.min_spend && baseTotal < c.min_spend) return false;
      return true;
    }
    return false;
  }

  // 对一组券按固定顺序结算，并返回逐步明细 steps，便于界面解释"怎么算出来的"
  function _apply(cart, menu, cs, baseTotal) {
    var adjustedUnit = {};
    for (var code in cart) {
      if (cart.hasOwnProperty(code)) adjustedUnit[code] = menu[code].price;
    }
    var steps = [];
    var running = baseTotal;
    // 1) 单品改价：每个单品取可适用的最低改价
    cs.forEach(function (c) {
      if (c.kind === "item_price" && adjustedUnit.hasOwnProperty(c.target)) {
        var oldU = adjustedUnit[c.target];
        var newU = Math.min(oldU, c.fixed);
        if (newU < oldU - 1e-9) {
          var qty = cart[c.target] || 0;
          var before = running;
          adjustedUnit[c.target] = newU;
          running = 0;
          for (var c2 in cart) { if (cart.hasOwnProperty(c2)) running += adjustedUnit[c2] * cart[c2]; }
          steps.push({ label: "单品改价", detail: menu[c.target].name + " 单价 ¥" + oldU.toFixed(2) + " → ¥" + newU.toFixed(2) + "（×" + qty + "）", before: round2(before), after: round2(running), saved: round2((oldU - newU) * qty) });
        }
      }
    });
    // 用最新单价重算基准小计（没有单品改价时等价于 baseTotal）
    running = 0;
    for (var c3 in cart) { if (cart.hasOwnProperty(c3)) running += adjustedUnit[c3] * cart[c3]; }
    // 2) 组合价：从池中选取 min_count 件最便宜的参与组合（贪心）
    var bundleCoupons = cs.filter(function (c) { return c.kind === "bundle_price"; });
    var consumed = {};
    var gifts = [];
    bundleCoupons.forEach(function (c) {
      var pool = (c.bundle_items || []).filter(function (i) {
        return (cart[i] || 0) - (consumed[i] || 0) > 0;
      });
      if (pool.length < c.min_count) return;
      pool.sort(function (a, b) { return adjustedUnit[a] - adjustedUnit[b]; });
      var chosen = pool.slice(0, c.min_count);
      var original = 0;
      chosen.forEach(function (i) { original += adjustedUnit[i]; });
      var delta = round2((c.bundle_price || 0) - original);
      var before = running;
      running += delta;
      var names = chosen.map(function (i) { return menu[i].name + " ¥" + adjustedUnit[i].toFixed(2); }).join(" + ");
      steps.push({ label: c.desc, detail: "从券池任选最便宜的 " + c.min_count + " 件：" + names + " 改按组合价 ¥" + (c.bundle_price || 0).toFixed(2) + " 结算", before: round2(before), after: round2(running), saved: round2(-delta) });
      chosen.forEach(function (i) { consumed[i] = (consumed[i] || 0) + 1; });
    });
    // 3) 折扣（先于满减，基于折后金额，更保守）
    cs.forEach(function (c) {
      if (c.kind === "percent") {
        var before = running;
        running *= (1 - (c.discount || 0));
        steps.push({ label: c.desc, detail: "小计 ¥" + before.toFixed(2) + " ×" + (1 - (c.discount || 0)).toFixed(2) + "（减 " + ((c.discount || 0) * 100) + "%）", before: round2(before), after: round2(running), saved: round2(before - running) });
      }
    });
    // 4) 满减
    cs.forEach(function (c) {
      if (c.kind === "threshold" && running >= (c.threshold || 0)) {
        var before = running;
        running -= (c.reduce || 0);
        steps.push({ label: c.desc, detail: "小计 ¥" + before.toFixed(2) + " ≥ 门槛 ¥" + (c.threshold || 0).toFixed(2) + "，立减 ¥" + (c.reduce || 0).toFixed(2), before: round2(before), after: round2(running), saved: round2(before - running) });
      }
    });
    // 5) 赠品（不影响应付，仅作额外所得记录）
    cs.forEach(function (c) {
      if (c.kind === "free_gift" && (c.target === null || c.target === undefined || (cart[c.target] || 0) > 0)) {
        if (c.gift) {
          gifts.push(c.gift);
          steps.push({ label: "赠品", detail: "买 " + (c.target ? menu[c.target].name : "任意单品") + " 送 " + menu[c.gift].name + "（免费，不计入应付）", before: round2(running), after: round2(running), saved: 0, gift: true });
        }
      }
    });
    return { price: Math.max(round2(running), 0), gifts: gifts, steps: steps };
  }

  function priceWithCoupons(cart, menu, coupons) {
    var baseTotal = 0;
    for (var code in cart) {
      if (cart.hasOwnProperty(code)) baseTotal += menu[code].price * cart[code];
    }
    var stackable = coupons.filter(function (c) { return c.stackable && _applicable(c, cart, baseTotal); });
    var nonStack = coupons.filter(function (c) { return !c.stackable && _applicable(c, cart, baseTotal); });

    var candidateSets = [[]];
    nonStack.forEach(function (c) { candidateSets.push([c]); });
    if (stackable.length <= 12) {
      for (var r = 1; r <= stackable.length; r++) {
        combinations(stackable, r).forEach(function (combo) { candidateSets.push(combo); });
      }
    } else {
      candidateSets.push(stackable);
    }

    var bestPrice = baseTotal, bestGiftCount = 0, bestUsed = [], bestGifts = [], bestSteps = [];
    candidateSets.forEach(function (cs) {
      var rr = _apply(cart, menu, cs, baseTotal);
      var price = round2(rr.price);
      var gifts = rr.gifts;
      if (price < bestPrice - 1e-9 ||
          (Math.abs(price - bestPrice) <= 1e-9 && gifts.length > bestGiftCount)) {
        bestPrice = price;
        bestGiftCount = gifts.length;
        bestUsed = cs.map(function (c) { return c.coupon_id; });
        bestGifts = gifts;
        bestSteps = rr.steps;
      }
    });
    return [bestPrice, bestUsed, bestGifts, bestSteps, candidateSets.length];
  }

  function cheapestForWishlist(wishlist, menu, coupons) {
    var cart = {};
    wishlist.forEach(function (code) { if (menu[code]) cart[code] = 1; });
    if (Object.keys(cart).length === 0) return [];
    var r = priceWithCoupons(cart, menu, coupons);
    return [{ cart: cart, total: r[0], usedCoupons: r[1], gifts: r[2], steps: r[3], tried: r[4] }];
  }


  function menuFromJson(data) {
    var menu = {};
    var meals = (data && (data.meals || data.items)) || [];
    meals.forEach(function (it) {
      menu[it.code] = {
        code: it.code, name: it.name || it.code,
        price: Number(it.price), tags: it.tags || []
      };
    });
    return menu;
  }

  function couponsFromJson(data) {
    return ((data && data.coupons) || []).map(function (c) {
      return {
        coupon_id: c.id, kind: c.kind, target: c.target, fixed: c.fixed,
        discount: c.discount, min_spend: c.min_spend, threshold: c.threshold,
        reduce: c.reduce, bundle_items: c.bundle_items, min_count: c.min_count || 2,
        bundle_price: c.bundle_price, gift: c.gift,
        stackable: !!c.stackable, desc: c.desc || ""
      };
    });
  }

  // 把方案拆成可渲染的明细行（供界面使用）
  function planLines(plan, menu) {
    var lines = [];
    for (var code in plan.cart) {
      if (!plan.cart.hasOwnProperty(code)) continue;
      var it = menu[code];
      lines.push({ name: it.name, qty: plan.cart[code], price: it.price, gift: false });
    }
    (plan.gifts || []).forEach(function (g) {
      lines.push({ name: menu[g] ? menu[g].name : g, qty: 1, price: 0, gift: true });
    });
    return lines;
  }

  return {
    round2: round2,
    priceWithCoupons: priceWithCoupons,
    cheapestForWishlist: cheapestForWishlist,
    menuFromJson: menuFromJson,
    couponsFromJson: couponsFromJson,
    planLines: planLines
  };
});
