const state = {
  month: null, // "YYYY-MM"
  categories: [],
  receipts: [],
  activeReceipt: null,
  itemsMonth: null,
  allItems: [],
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function fmtMoney(n) {
  return `$${Number(n || 0).toFixed(2)}`;
}

function currentMonthStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function shiftMonth(month, delta) {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(month) {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1, 1);
  return d.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

// ---------- Navigation ----------
const VALID_VIEWS = ["dashboard", "items", "upload", "categories"];

function setView(view, pushHash = true) {
  if (!VALID_VIEWS.includes(view)) view = "dashboard";
  $$(".nav-item[data-view]").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  $$(".view").forEach((section) => section.classList.toggle("active", section.id === `view-${view}`));
  if (pushHash && location.hash.slice(1) !== view) {
    location.hash = view;
  }
  if (view === "items") loadItems();
  if (view === "categories") renderCategoryList();
}

function viewFromHash() {
  return location.hash.slice(1) || "dashboard";
}

window.addEventListener("hashchange", () => setView(viewFromHash(), false));

$$(".nav-item[data-view]").forEach((btn) => {
  btn.addEventListener("click", () => setView(btn.dataset.view));
});
document.body.addEventListener("click", (e) => {
  const link = e.target.closest("a[data-view]");
  if (link) {
    e.preventDefault();
    setView(link.dataset.view);
  }
});

// ---------- Dashboard ----------
async function loadCategories() {
  const res = await fetch("/api/categories");
  state.categories = await res.json();
}

async function loadDashboard() {
  $("#month-label").textContent = monthLabel(state.month);

  const [receiptsRes, breakdownRes] = await Promise.all([
    fetch(`/api/receipts?month=${state.month}`),
    fetch(`/api/summary/${state.month}`),
  ]);
  state.receipts = await receiptsRes.json();
  const breakdown = await breakdownRes.json();

  const total = breakdown.reduce((sum, row) => sum + Number(row.total), 0);
  $("#month-total-value").textContent = fmtMoney(total);

  renderBreakdown(breakdown, total);
  renderReceipts(state.receipts);
}

function renderBreakdown(breakdown, total) {
  const el = $("#breakdown");
  el.innerHTML = "";
  if (!breakdown.length) return;

  for (const row of breakdown) {
    const pct = total > 0 ? (Number(row.total) / total) * 100 : 0;
    const div = document.createElement("div");
    div.className = "breakdown-row";
    div.innerHTML = `
      <span class="breakdown-name">${row.category || "Uncategorized"} &nbsp; <span class="breakdown-amount">${fmtMoney(row.total)}</span></span>
      <span class="breakdown-track"><span class="breakdown-fill" style="width:${pct}%;background:${row.color}"></span></span>
    `;
    el.appendChild(div);
  }
}

function renderReceipts(receipts) {
  const list = $("#receipts-list");
  list.innerHTML = "";
  $("#empty-state").hidden = receipts.length > 0;

  receipts.forEach((r, i) => {
    const row = document.createElement("div");
    row.className = "ledger-row clickable";
    row.style.animation = "rowReveal 0.32s ease both";
    row.style.animationDelay = `${Math.min(i, 14) * 28}ms`;
    const itemsPreview = r.line_items.slice(0, 2).map((i) => i.description).join(", ") +
      (r.line_items.length > 2 ? `, +${r.line_items.length - 2} more` : "");
    row.innerHTML = `
      <span>${r.purchase_date || "—"}</span>
      <span>${r.merchant || "Unknown"}</span>
      <span>${itemsPreview || "—"}</span>
      <span class="num">${fmtMoney(r.total)}</span>
      <span class="status-pill status-${r.status}">${r.status.replace("_", " ")}</span>
    `;
    row.addEventListener("click", () => openReview(r.id));
    list.appendChild(row);
  });
}

$("#month-prev").addEventListener("click", () => {
  state.month = shiftMonth(state.month, -1);
  loadDashboard();
});
$("#month-next").addEventListener("click", () => {
  state.month = shiftMonth(state.month, 1);
  loadDashboard();
});

// ---------- Upload ----------
const dropzone = $("#dropzone");
const fileInput = $("#file-input");

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
  })
);
dropzone.addEventListener("drop", (e) => uploadFiles(e.dataTransfer.files));
fileInput.addEventListener("change", (e) => uploadFiles(e.target.files));

async function uploadFiles(fileList) {
  if (!fileList.length) return;
  const formData = new FormData();
  for (const file of fileList) formData.append("files", file);

  const queue = $("#upload-queue");
  const entry = document.createElement("div");
  entry.className = "upload-queue-item";
  entry.innerHTML = `<span>${fileList.length} file(s) uploading…</span>`;
  queue.prepend(entry);

  try {
    const res = await fetch("/api/receipts/upload", { method: "POST", body: formData });
    if (!res.ok) throw new Error(await res.text());
    entry.innerHTML = `<span>${fileList.length} file(s) sent for extraction</span><span>✓</span>`;
    if (state.month) loadDashboard();
  } catch (err) {
    entry.innerHTML = `<span>Upload failed</span><span>${err.message}</span>`;
  }
}

// ---------- Categories ----------
async function renderCategoryList() {
  await loadCategories();
  const el = $("#cat-list");
  el.innerHTML = "";
  for (const c of state.categories) {
    const row = document.createElement("div");
    row.className = "cat-row";
    row.innerHTML = `
      <span class="cat-swatch" style="background:${c.color}"></span>
      <span>${c.name}</span>
      <button data-id="${c.id}">Remove</button>
    `;
    row.querySelector("button").addEventListener("click", async () => {
      await fetch(`/api/categories/${c.id}`, { method: "DELETE" });
      renderCategoryList();
    });
    el.appendChild(row);
  }
}

$("#cat-add-btn").addEventListener("click", async () => {
  const name = $("#cat-name").value.trim();
  if (!name) return;
  const color = $("#cat-color").value;
  await fetch("/api/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, color }),
  });
  $("#cat-name").value = "";
  renderCategoryList();
});

// ---------- Review overlay ----------
function categoryOptionsHtml(selectedId) {
  let html = `<option value="">—</option>`;
  for (const c of state.categories) {
    html += `<option value="${c.id}" ${c.id === selectedId ? "selected" : ""}>${c.name}</option>`;
  }
  return html;
}

function addItemRow(item = {}) {
  const tr = document.createElement("tr");
  tr.dataset.itemId = item.id || "";
  tr.innerHTML = `
    <td><input type="text" class="item-desc" value="${item.description || ""}" /></td>
    <td><input type="number" step="0.01" class="item-qty" value="${item.quantity || 1}" style="width:60px" /></td>
    <td><input type="number" step="0.01" class="item-price" value="${item.price || 0}" style="width:80px" /></td>
    <td><select class="item-cat">${categoryOptionsHtml(item.category_id || item.category?.id || null)}</select></td>
    <td><button class="remove-item">&times;</button></td>
  `;
  tr.querySelector(".remove-item").addEventListener("click", () => tr.remove());
  $("#items-body").appendChild(tr);
}

async function openReview(receiptId) {
  const res = await fetch(`/api/receipts/${receiptId}`);
  const receipt = await res.json();
  state.activeReceipt = receipt;

  const fileUrl = `/files/${receipt.stored_filename}`;
  const isPdf = receipt.stored_filename.toLowerCase().endsWith(".pdf");
  $("#review-image").hidden = isPdf;
  $("#review-pdf").hidden = !isPdf;
  if (isPdf) {
    $("#review-pdf").src = fileUrl;
  } else {
    $("#review-image").src = fileUrl;
  }

  $("#f-merchant").value = receipt.merchant || "";
  $("#f-date").value = receipt.purchase_date || "";
  $("#f-subtotal").value = receipt.subtotal ?? "";
  $("#f-tax").value = receipt.tax ?? "";
  $("#f-total").value = receipt.total ?? "";

  $("#items-body").innerHTML = "";
  for (const item of receipt.line_items) addItemRow(item);

  $("#review-error").hidden = true;
  if (receipt.status === "failed" && receipt.error_message) {
    $("#review-error").hidden = false;
    $("#review-error").textContent = receipt.error_message;
  }

  $("#review-overlay").hidden = false;
}

$("#review-close").addEventListener("click", () => ($("#review-overlay").hidden = true));
$("#add-item").addEventListener("click", () => addItemRow());

function collectItems() {
  const rows = $$("#items-body tr");
  const items = [];
  for (const row of rows) {
    const description = row.querySelector(".item-desc").value.trim();
    if (!description) continue;
    items.push({
      id: row.dataset.itemId ? Number(row.dataset.itemId) : undefined,
      description,
      quantity: Number(row.querySelector(".item-qty").value) || 1,
      price: Number(row.querySelector(".item-price").value) || 0,
      category_id: row.querySelector(".item-cat").value ? Number(row.querySelector(".item-cat").value) : null,
    });
  }
  return items;
}

async function saveReceipt(confirm) {
  const payload = {
    merchant: $("#f-merchant").value || null,
    purchase_date: $("#f-date").value || null,
    subtotal: $("#f-subtotal").value ? Number($("#f-subtotal").value) : null,
    tax: $("#f-tax").value ? Number($("#f-tax").value) : null,
    total: $("#f-total").value ? Number($("#f-total").value) : null,
    line_items: collectItems(),
    confirm,
  };
  const res = await fetch(`/api/receipts/${state.activeReceipt.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    $("#review-error").hidden = false;
    $("#review-error").textContent = "Couldn't save — check the fields above.";
    return;
  }
  $("#review-overlay").hidden = true;
  loadDashboard();
}

$("#save-draft").addEventListener("click", () => saveReceipt(false));
$("#confirm-receipt").addEventListener("click", () => saveReceipt(true));
$("#delete-receipt").addEventListener("click", async () => {
  if (!confirm("Delete this receipt permanently?")) return;
  await fetch(`/api/receipts/${state.activeReceipt.id}`, { method: "DELETE" });
  $("#review-overlay").hidden = true;
  loadDashboard();
});

// ---------- Items (flat, searchable, deletable) ----------
async function loadItems() {
  if (!state.itemsMonth) state.itemsMonth = state.month || currentMonthStr();
  $("#items-month-label").textContent = monthLabel(state.itemsMonth);

  const res = await fetch(`/api/receipts/items/${state.itemsMonth}`);
  state.allItems = await res.json();
  renderItems();
}

function renderItems() {
  const query = $("#items-search").value.trim().toLowerCase();
  const filtered = state.allItems.filter((item) => {
    if (!query) return true;
    return (
      item.description.toLowerCase().includes(query) ||
      (item.merchant || "").toLowerCase().includes(query)
    );
  });

  const list = $("#items-list");
  list.innerHTML = "";
  $("#items-empty-state").hidden = filtered.length > 0;

  for (const item of filtered) {
    const row = document.createElement("div");
    row.className = "ledger-row";
    const catColor = item.category?.color || "#6b7280";
    const catName = item.category?.name || "—";
    row.innerHTML = `
      <span>${item.purchase_date || "—"}</span>
      <span>${item.merchant || "Unknown"}</span>
      <span>${item.description}</span>
      <span class="num">${fmtMoney(item.price)}</span>
      <span><span class="item-cat-pill" style="background:${catColor}22;color:${catColor}">${catName}</span></span>
      <button class="item-delete-btn" data-id="${item.id}" title="Delete this item">&times;</button>
    `;
    row.querySelector(".item-delete-btn").addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(`Delete "${item.description}" (${fmtMoney(item.price)})? This can't be undone.`)) return;
      await fetch(`/api/receipts/items/${item.id}`, { method: "DELETE" });
      loadItems();
      if (state.month) loadDashboard(); // keep ledger totals in sync if open
    });
    list.appendChild(row);
  }
}

$("#items-search").addEventListener("input", renderItems);

$("#items-month-prev").addEventListener("click", () => {
  state.itemsMonth = shiftMonth(state.itemsMonth, -1);
  loadItems();
});
$("#items-month-next").addEventListener("click", () => {
  state.itemsMonth = shiftMonth(state.itemsMonth, 1);
  loadItems();
});

// ---------- Init ----------
(async function init() {
  state.month = currentMonthStr();
  await loadCategories();
  await loadDashboard();
  setView(viewFromHash(), false);
})();
