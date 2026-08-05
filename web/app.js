"use strict";

const state = {
  dashboard: null,
  updateStatus: null,
  selectedEntity: null,
  selectedSupplierIds: [],
  selectedCategoryTotal: "",
};

const elements = {};

function numberValue(value) {
  return Number(value ?? 0);
}

function formatQuantity(value) {
  return new Intl.NumberFormat("ja-JP", { maximumFractionDigits: 2 }).format(
    numberValue(value),
  );
}

function formatRate(value) {
  if (value === null || value === undefined) return "算出不可";
  return `${(numberValue(value) * 100).toFixed(2)}%`;
}

function formatPointDifference(value) {
  if (value === null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(2)} pt`;
}

function previousYearMonth(targetMonth) {
  const [year, month] = targetMonth.split("-");
  return `${Number(year) - 1}-${month}`;
}

function monthLabel(targetMonth) {
  const [year, month] = targetMonth.split("-");
  return `${year}年${Number(month)}月`;
}

function selectedMonths(entity) {
  const start = elements.startMonth.value;
  const end = elements.endMonth.value;
  if (!start || !end || start > end) return [];
  return entity.months.filter(
    (item) => item.targetMonth >= start && item.targetMonth <= end,
  );
}

function summarizePeriod(months) {
  const available = months.filter((item) => !item.statuses.includes("missing"));
  const returnQuantity = available.reduce(
    (total, item) => total + numberValue(item.returnQuantity),
    0,
  );
  const shipmentQuantity = available.reduce(
    (total, item) => total + numberValue(item.shipmentQuantity),
    0,
  );
  return {
    returnQuantity,
    shipmentQuantity,
    defectiveRate:
      shipmentQuantity === 0 ? null : returnQuantity / shipmentQuantity,
  };
}

function entityLabel(entity) {
  if (!entity) return "表示対象なし";
  if (entity.entityType === "supplier") {
    return `[${entity.category || "区分未登録"}] ${entity.supplierIds[0]}｜${entity.displayName}`;
  }
  if (entity.entityType === "combined") {
    return window.SupplierQualityCombine.labelCombinedSelection(
      entity,
      elements.mode.value,
    );
  }
  return `[${entity.category || "区分未登録"}] ${entity.displayName}`;
}

function supplierIdSortKey(supplierId) {
  const trimmed = String(supplierId).trim();
  if (/^\d+$/.test(trimmed)) {
    return [0, Number(trimmed), ""];
  }
  return [1, 0, trimmed];
}

function compareEntitiesForOptions(left, right) {
  if (left.entityType === "supplier" && right.entityType === "supplier") {
    const leftKey = supplierIdSortKey(left.supplierIds[0]);
    const rightKey = supplierIdSortKey(right.supplierIds[0]);
    if (leftKey[0] !== rightKey[0]) return leftKey[0] - rightKey[0];
    if (leftKey[0] === 0) return leftKey[1] - rightKey[1];
    return leftKey[2].localeCompare(rightKey[2], "ja");
  }
  return entityLabel(left).localeCompare(entityLabel(right), "ja");
}

function supplierEntities() {
  return (state.dashboard?.entities ?? []).filter(
    (entity) => entity.entityType === "supplier",
  );
}

function filteredSupplierCandidates() {
  const category = elements.category.value;
  const query = elements.search.value.trim().toLowerCase();
  return supplierEntities()
    .filter((entity) => {
      if (category && !entity.category.split("／").includes(category)) {
        return false;
      }
      if (!query) return true;
      const searchable = [
        entity.displayName,
        ...entity.supplierIds,
        ...(entity.supplierNames ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return searchable.includes(query);
    })
    .slice()
    .sort(compareEntitiesForOptions);
}

function filteredGroupCandidates() {
  const category = elements.category.value;
  const query = elements.search.value.trim().toLowerCase();
  return (state.dashboard?.entities ?? [])
    .filter((entity) => {
      if (entity.entityType !== "group") return false;
      if (category && !entity.category.split("／").includes(category)) {
        return false;
      }
      if (!query) return true;
      const searchable = [
        entity.displayName,
        ...entity.supplierIds,
        ...(entity.supplierNames ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return searchable.includes(query);
    })
    .slice()
    .sort(compareEntitiesForOptions);
}

function categoryTotalOptions() {
  return [...new Set(
    supplierEntities().flatMap((entity) =>
      entity.category.split("／").filter(Boolean),
    ),
  )].sort();
}

function suppliersInCategory(category) {
  return supplierEntities().filter((entity) =>
    entity.category.split("／").includes(category),
  );
}

function updateCategoryOptions() {
  const current = elements.category.value;
  const mode = elements.mode.value;
  let categories = [];
  if (mode === "supplier" || mode === "category") {
    categories = categoryTotalOptions();
  } else {
    categories = [...new Set(
      (state.dashboard?.entities ?? [])
        .filter((entity) => entity.entityType === "group")
        .flatMap((entity) => entity.category.split("／"))
        .filter(Boolean),
    )].sort();
  }
  elements.category.replaceChildren(
    new Option("すべて", ""),
    ...categories.map((category) => new Option(category, category)),
  );
  if (categories.includes(current)) elements.category.value = current;
}

function setControlVisibility() {
  const mode = elements.mode.value;
  const supplierMode = mode === "supplier";
  const categoryMode = mode === "category";

  elements.entityCheckboxesField.hidden = !supplierMode;
  elements.entityField.hidden = supplierMode;
  elements.categoryField.hidden = categoryMode;
  elements.searchField.hidden = categoryMode;
  elements.entityLabel.textContent = categoryMode
    ? "合算区分"
    : "仕入先／グループ";
}

function updateEntityCheckboxes() {
  const candidates = filteredSupplierCandidates();
  const selected = new Set(state.selectedSupplierIds);
  elements.entityCheckboxes.replaceChildren(
    ...candidates.map((entity) => {
      const supplierId = entity.supplierIds[0];
      const label = document.createElement("label");
      label.className = "entity-check";
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = supplierId;
      input.checked = selected.has(supplierId);
      input.addEventListener("change", () => {
        if (input.checked) {
          if (!state.selectedSupplierIds.includes(supplierId)) {
            state.selectedSupplierIds.push(supplierId);
          }
        } else {
          state.selectedSupplierIds = state.selectedSupplierIds.filter(
            (item) => item !== supplierId,
          );
        }
        syncSelectionFromControls();
      });
      const text = document.createElement("span");
      text.textContent = entityLabel(entity);
      label.append(input, text);
      return label;
    }),
  );
}

function updateEntitySelect() {
  const mode = elements.mode.value;
  if (mode === "group") {
    const candidates = filteredGroupCandidates();
    const current = elements.entity.value;
    elements.entity.replaceChildren(
      ...candidates.map(
        (entity) => new Option(entityLabel(entity), entity.entityId),
      ),
    );
    if (candidates.some((entity) => entity.entityId === current)) {
      elements.entity.value = current;
    }
    return;
  }
  if (mode === "category") {
    const current =
      state.selectedCategoryTotal || elements.entity.value;
    const categories = categoryTotalOptions();
    elements.entity.replaceChildren(
      ...categories.map((category) => new Option(category, category)),
    );
    if (categories.includes(current)) {
      elements.entity.value = current;
      state.selectedCategoryTotal = current;
    } else if (categories.length) {
      elements.entity.value = categories[0];
      state.selectedCategoryTotal = categories[0];
    } else {
      state.selectedCategoryTotal = "";
    }
  }
}

function buildSelectedEntity() {
  const mode = elements.mode.value;
  if (mode === "group") {
    return (
      state.dashboard.entities.find(
        (entity) => entity.entityId === elements.entity.value,
      ) ?? null
    );
  }
  if (mode === "category") {
    const category = state.selectedCategoryTotal || elements.entity.value;
    if (!category) return null;
    const combined = window.SupplierQualityCombine.combineEntityMonths(
      suppliersInCategory(category),
    );
    if (!combined) return null;
    combined.displayName = `${category} 合算`;
    combined.category = category;
    return combined;
  }
  const selected = state.selectedSupplierIds
    .map((supplierId) =>
      supplierEntities().find(
        (entity) => entity.supplierIds[0] === supplierId,
      ),
    )
    .filter(Boolean)
    .sort(compareEntitiesForOptions);
  if (!selected.length) return null;
  if (selected.length === 1) return selected[0];
  const combined = window.SupplierQualityCombine.combineEntityMonths(selected);
  combined.displayName = window.SupplierQualityCombine.labelCombinedSelection(
    combined,
    mode,
  );
  return combined;
}

function syncSelectionFromControls() {
  if (elements.mode.value === "category") {
    state.selectedCategoryTotal = elements.entity.value;
  }
  state.selectedEntity = buildSelectedEntity();
  render();
}

function refreshSelectors() {
  setControlVisibility();
  updateCategoryOptions();
  if (elements.mode.value === "supplier") {
    state.selectedSupplierIds = state.selectedSupplierIds.filter((supplierId) =>
      supplierEntities().some(
        (entity) => entity.supplierIds[0] === supplierId,
      ),
    );
    updateEntityCheckboxes();
  } else {
    updateEntitySelect();
  }
  syncSelectionFromControls();
}

function statusLabels(month) {
  const labels = [];
  if (month.statuses.includes("missing")) labels.push("欠損月");
  if (month.statuses.includes("zero_shipment")) labels.push("出荷数0");
  if (month.statuses.includes("in_progress")) labels.push("集計途中");
  if (month.statuses.includes("abnormal")) labels.push("100％以上");
  return labels.length ? labels.join("／") : "正常";
}

function renderDetails(months) {
  elements.detailBody.replaceChildren(
    ...months.map((month) => {
      const row = document.createElement("tr");
      const exceeded =
        month.defectiveRate !== null && numberValue(month.defectiveRate) >= 0.01;
      const values = [
        monthLabel(month.targetMonth),
        formatQuantity(month.shipmentQuantity),
        formatQuantity(month.returnQuantity),
        formatRate(month.defectiveRate),
        month.defectiveRate === null ? "判定不能" : exceeded ? "目標超過" : "目標内",
        statusLabels(month),
        month.warningCodes.length ? month.warningCodes.join(", ") : "—",
      ];
      values.forEach((value, index) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        if (index === 4 && exceeded) cell.className = "status-warning";
        if (index === 5 && month.statuses.includes("abnormal")) {
          cell.className = "status-danger";
        }
        row.append(cell);
      });
      return row;
    }),
  );
}

function renderKpis(entity, months) {
  const latestMonth = entity.months.find(
    (item) => item.targetMonth === state.dashboard.latestDataMonth,
  );
  const priorMonth = entity.months.find(
    (item) =>
      item.targetMonth === previousYearMonth(state.dashboard.latestDataMonth),
  );
  const period = summarizePeriod(months);
  const priorAvailable =
    priorMonth && !priorMonth.statuses.includes("missing");
  const latestAvailable =
    latestMonth && !latestMonth.statuses.includes("missing");

  elements.latestRate.textContent = latestAvailable
    ? formatRate(latestMonth.defectiveRate)
    : "—";
  elements.previousRate.textContent = priorAvailable
    ? formatRate(priorMonth.defectiveRate)
    : "前年同月データなし";
  const difference =
    latestAvailable &&
    latestMonth.defectiveRate !== null &&
    priorAvailable &&
    priorMonth.defectiveRate !== null
      ? numberValue(latestMonth.defectiveRate) - numberValue(priorMonth.defectiveRate)
      : null;
  elements.rateDifference.textContent = formatPointDifference(difference);
  elements.latestReturns.textContent = latestAvailable
    ? formatQuantity(latestMonth.returnQuantity)
    : "—";
  elements.latestShipments.textContent = latestAvailable
    ? formatQuantity(latestMonth.shipmentQuantity)
    : "—";
  elements.periodRate.textContent = formatRate(period.defectiveRate);
}

function clearDashboard(message) {
  elements.screenMessage.textContent = message;
  elements.selectedEntityName.textContent = "表示対象なし";
  elements.detailBody.replaceChildren();
  ["latestRate", "previousRate", "rateDifference", "latestReturns", "latestShipments", "periodRate"]
    .forEach((key) => { elements[key].textContent = "—"; });
  window.renderTrendChart?.(elements.trendChart, []);
}

function render() {
  const entity = state.selectedEntity;
  if (!entity) {
    const mode = elements.mode.value;
    clearDashboard(
      mode === "supplier"
        ? "仕入先を1件以上選択してください。"
        : "条件に一致する仕入先またはグループがありません。",
    );
    return;
  }
  if (elements.startMonth.value > elements.endMonth.value) {
    clearDashboard("開始月は終了月以前を指定してください。");
    return;
  }

  const months = selectedMonths(entity);
  const messages = [];
  if (state.updateStatus?.status === "failure") {
    messages.push("最新更新に失敗しました。前回正常データを表示しています。");
  }
  if (months.some((item) => item.warningCodes.length)) {
    messages.push("対象期間に警告があります。詳細表を確認してください。");
  }
  if (
    months.length === 0 ||
    months.every((item) => item.statuses.includes("missing"))
  ) {
    messages.push("対象期間に該当データがありません。");
  }
  const latest = entity.months.find(
    (item) => item.targetMonth === state.dashboard.latestDataMonth,
  );
  if (latest?.statuses.includes("in_progress")) {
    messages.push("最新月は集計途中です。前年同月比較も途中値です。");
  }
  elements.screenMessage.textContent = messages.join(" ");
  elements.selectedEntityName.textContent = entityLabel(entity);
  renderKpis(entity, months);
  renderDetails(months);
  window.renderTrendChart?.(elements.trendChart, months);
}

async function loadDashboard() {
  const useExample = new URLSearchParams(window.location.search).get("example") === "1";
  const dashboardPath = useExample
    ? "data/dashboard-data.example.json"
    : "data/dashboard-data.json";
  const statusPath = useExample
    ? "data/update-status.example.json"
    : "data/update-status.json";
  const [dashboardResponse, statusResponse] = await Promise.all([
    fetch(dashboardPath, { cache: "no-store" }),
    fetch(statusPath, { cache: "no-store" }),
  ]);
  if (!dashboardResponse.ok) throw new Error("Dashboard data not found");
  state.dashboard = await dashboardResponse.json();
  state.updateStatus = statusResponse.ok ? await statusResponse.json() : null;

  elements.generatedAt.textContent = new Date(
    state.dashboard.generatedAt,
  ).toLocaleString("ja-JP");
  elements.latestMonth.textContent = monthLabel(state.dashboard.latestDataMonth);
  elements.warningCount.textContent = String(
    state.dashboard.warningCount ?? state.dashboard.warnings.length,
  );
  elements.startMonth.value = state.dashboard.defaultPeriod.startMonth;
  elements.endMonth.value = state.dashboard.defaultPeriod.endMonth;
  refreshSelectors();
}

function bindElements() {
  const ids = [
    "generated-at", "latest-month", "warning-count", "mode", "category",
    "search", "entity", "start-month", "end-month", "screen-message",
    "latest-rate", "previous-rate", "rate-difference", "latest-returns",
    "latest-shipments", "period-rate", "selected-entity-name", "trend-chart",
    "detail-body", "entity-checkboxes", "select-all", "clear-selection", "entity-label",
    "category-field", "search-field", "entity-field", "entity-checkboxes-field",
  ];
  ids.forEach((id) => {
    const key = id.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    elements[key] = document.getElementById(id);
  });
}

function bindEvents() {
  elements.mode.addEventListener("change", () => {
    state.selectedSupplierIds = [];
    state.selectedCategoryTotal = "";
    refreshSelectors();
  });
  elements.category.addEventListener("change", () => {
    if (elements.mode.value === "supplier") {
      updateEntityCheckboxes();
      syncSelectionFromControls();
      return;
    }
    refreshSelectors();
  });
  elements.search.addEventListener("input", () => {
    if (elements.mode.value === "supplier") {
      updateEntityCheckboxes();
      return;
    }
    refreshSelectors();
  });
  elements.entity.addEventListener("change", syncSelectionFromControls);
  elements.selectAll.addEventListener("click", () => {
    const visibleIds = filteredSupplierCandidates().map(
      (entity) => entity.supplierIds[0],
    );
    const selected = new Set(state.selectedSupplierIds);
    for (const supplierId of visibleIds) {
      selected.add(supplierId);
    }
    state.selectedSupplierIds = [...selected];
    updateEntityCheckboxes();
    syncSelectionFromControls();
  });
  elements.clearSelection.addEventListener("click", () => {
    state.selectedSupplierIds = [];
    updateEntityCheckboxes();
    syncSelectionFromControls();
  });
  elements.startMonth.addEventListener("change", render);
  elements.endMonth.addEventListener("change", render);
  window.addEventListener("resize", () => window.resizeTrendChart?.());
}

document.addEventListener("DOMContentLoaded", async () => {
  bindElements();
  bindEvents();
  try {
    await loadDashboard();
  } catch {
    clearDashboard("表示データが未作成です。バッチを実行してください。");
  }
});
