const M = require("../../utils/optimizer.js");
const D = require("../../utils/sample_data.js");

Page({
  data: {
    menuList: [],
    couponList: [],
    activeTab: "wish",
    budget: "20",
    result: null,
    budgetResult: [],
    kindName: {
      item_price: "单品价", percent: "折扣",
      threshold: "满减", bundle_price: "组合价", free_gift: "赠品"
    }
  },

  onLoad() {
    const menu = M.menuFromJson(D.MEALS);
    const coupons = M.couponsFromJson(D.COUPONS);
    const all = D.MEALS.meals.map(function (it) {
      return {
        code: it.code, name: it.name, price: it.price, tags: it.tags || [],
        cat: (it.tags && it.tags[0]) || "其他", sel: false
      };
    });
    const seen = [];
    all.forEach(function (it) { if (seen.indexOf(it.cat) < 0) seen.push(it.cat); });
    const catList = [{ key: "all", name: "全部" }].concat(
      seen.map(function (c) { return { key: c, name: c }; })
    );
    const couponList = coupons.map(function (c) {
      return { kind: c.kind, desc: c.desc, stackable: c.stackable };
    });
    this.menu = menu;
    this.coupons = coupons;
    this.couponMap = {};
    var self = this;
    coupons.forEach(function (c) { self.couponMap[c.coupon_id] = c; });
    this.allMenu = all;
    this.setData({ catList: catList, currentCat: "all", showList: all.slice(), couponList: couponList });
  },

  switchCat(e) {
    const cat = e.currentTarget.dataset.cat;
    const showList = (cat === "all")
      ? this.allMenu.slice()
      : this.allMenu.filter(function (m) { return m.cat === cat; });
    this.setData({ currentCat: cat, showList: showList.map(function (m) { return Object.assign({}, m); }) });
  },

  refreshShow() {
    const cat = this.data.currentCat;
    const showList = (cat === "all" ? this.allMenu : this.allMenu.filter(function (m) { return m.cat === cat; }))
      .map(function (m) { return Object.assign({}, m); });
    this.setData({ showList: showList });
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab });
  },

  toggleItem(e) {
    const code = e.currentTarget.dataset.code;
    const all = this.allMenu.slice();
    const item = all.find(function (m) { return m.code === code; });
    if (item) item.sel = !item.sel;
    this.allMenu = all;
    this.refreshShow();
  },

  selectAll() {
    const self = this;
    this.allMenu = this.allMenu.map(function (m) {
      const o = Object.assign({}, m);
      if (self.data.currentCat === "all" || o.cat === self.data.currentCat) o.sel = true;
      return o;
    });
    this.refreshShow();
  },

  clearAll() {
    const self = this;
    this.allMenu = this.allMenu.map(function (m) {
      const o = Object.assign({}, m);
      if (self.data.currentCat === "all" || o.cat === self.data.currentCat) o.sel = false;
      return o;
    });
    this.refreshShow();
  },

  buildPlan(plan) {
    let base = 0;
    for (const c in plan.cart) base += this.menu[c].price * plan.cart[c];
    const saved = M.round2(base - plan.total);
    const lines = M.planLines(plan, this.menu).map(function (l) {
      return { name: l.name, qty: l.qty, price: l.price.toFixed(2), gift: l.gift };
    });
    const used = (plan.usedCoupons || []).map((id) => {
      return this.couponMap[id] ? this.couponMap[id].desc : id;
    }).join("、");
    const steps = plan.steps || [];
    const explain = steps.length ? steps.map((s) => ({
      label: s.label, detail: s.detail,
      before: s.before.toFixed(2), after: s.after.toFixed(2),
      saved: s.saved.toFixed(2), gift: !!s.gift
    })) : [];
    return {
      total: plan.total.toFixed(2), base: base.toFixed(2),
      saved: saved.toFixed(2), lines: lines, used: used || "未用到券",
      explain: explain, tried: plan.tried || 0
    };
  },

  computeWish() {
    const codes = this.allMenu.filter(function (m) { return m.sel; }).map(function (m) { return m.code; });
    if (!codes.length) { wx.showToast({ title: "先勾选想吃的", icon: "none" }); return; }
    const plan = M.cheapestForWishlist(codes, this.menu, this.coupons)[0];
    this.setData({ result: this.buildPlan(plan) });
  },

  onBudgetInput(e) {
    this.setData({ budget: e.detail.value });
  },

  computeBudget() {
    const b = parseFloat(this.data.budget);
    if (!(b > 0)) { wx.showToast({ title: "请输入有效预算", icon: "none" }); return; }
    const plans = M.budgetCombos(this.menu, this.coupons, b, 3);
    const list = plans.map((p, i) => {
      const names = M.planLines(p, this.menu).map(function (l) {
        return l.name + (l.gift ? "(赠)" : "");
      }).join(" + ");
      const used = (p.usedCoupons || []).map((id) => {
        return this.couponMap[id] ? this.couponMap[id].desc : id;
      }).join("、");
      return { idx: i + 1, total: p.total.toFixed(2), names: names, saved: p.saved.toFixed(2), used: used || "无" };
    });
    this.setData({ budgetResult: list });
  }
});
