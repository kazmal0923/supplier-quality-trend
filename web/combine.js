"use strict";

function combineNumberValue(value) {
  return Number(value ?? 0);
}

function combineEntityMonths(entities) {
  if (!Array.isArray(entities) || entities.length === 0) {
    return null;
  }

  const monthMap = new Map();
  for (const entity of entities) {
    for (const month of entity.months ?? []) {
      let bucket = monthMap.get(month.targetMonth);
      if (!bucket) {
        bucket = {
          targetMonth: month.targetMonth,
          returnQuantity: 0,
          shipmentQuantity: 0,
          presentCount: 0,
          statuses: new Set(),
          warningCodes: new Set(),
        };
        monthMap.set(month.targetMonth, bucket);
      }
      if ((month.statuses ?? []).includes("missing")) {
        continue;
      }
      bucket.presentCount += 1;
      bucket.returnQuantity += combineNumberValue(month.returnQuantity);
      bucket.shipmentQuantity += combineNumberValue(month.shipmentQuantity);
      for (const status of month.statuses ?? []) {
        if (status !== "missing") bucket.statuses.add(status);
      }
      for (const code of month.warningCodes ?? []) {
        bucket.warningCodes.add(code);
      }
    }
  }

  const months = [...monthMap.values()]
    .sort((left, right) => left.targetMonth.localeCompare(right.targetMonth))
    .map((bucket) => {
      if (bucket.presentCount === 0) {
        return {
          targetMonth: bucket.targetMonth,
          returnQuantity: "0",
          shipmentQuantity: "0",
          defectiveRate: null,
          statuses: ["missing"],
          warningCodes: ["MISSING_MONTH"],
        };
      }
      const defectiveRate =
        bucket.shipmentQuantity === 0
          ? null
          : bucket.returnQuantity / bucket.shipmentQuantity;
      const statuses = [...bucket.statuses];
      if (
        bucket.shipmentQuantity === 0 &&
        !statuses.includes("zero_shipment")
      ) {
        statuses.push("zero_shipment");
      }
      if (
        defectiveRate !== null &&
        defectiveRate >= 1 &&
        !statuses.includes("abnormal")
      ) {
        statuses.push("abnormal");
      }
      return {
        targetMonth: bucket.targetMonth,
        returnQuantity: String(bucket.returnQuantity),
        shipmentQuantity: String(bucket.shipmentQuantity),
        defectiveRate:
          defectiveRate === null ? null : String(defectiveRate),
        statuses,
        warningCodes: [...bucket.warningCodes],
      };
    });

  const supplierIds = [];
  const supplierNames = [];
  const categories = new Set();
  for (const entity of entities) {
    for (const supplierId of entity.supplierIds ?? []) {
      if (!supplierIds.includes(supplierId)) supplierIds.push(supplierId);
    }
    for (const name of entity.supplierNames ?? [entity.displayName]) {
      if (name && !supplierNames.includes(name)) supplierNames.push(name);
    }
    for (const part of String(entity.category || "").split("／")) {
      if (part) categories.add(part);
    }
  }

  return {
    entityId: `combined:${supplierIds.join("+") || "empty"}`,
    entityType: "combined",
    displayName: "",
    category: [...categories].join("／"),
    supplierIds,
    supplierNames,
    months,
  };
}

function labelCombinedSelection(entity, mode) {
  if (!entity) return "表示対象なし";
  if (mode === "category") {
    return `[${entity.category || "区分未登録"}] 区分合算（${entity.supplierIds.length}件）`;
  }
  if (entity.supplierIds.length === 1) {
    return `[${entity.category || "区分未登録"}] ${entity.supplierIds[0]}｜${entity.supplierNames[0] || entity.displayName}`;
  }
  const preview = entity.supplierIds.slice(0, 5).join(", ");
  const more =
    entity.supplierIds.length > 5
      ? ` 他${entity.supplierIds.length - 5}件`
      : "";
  return `選択 ${entity.supplierIds.length}件（${preview}${more}）`;
}

const SupplierQualityCombine = {
  combineEntityMonths,
  labelCombinedSelection,
};

if (typeof window !== "undefined") {
  window.SupplierQualityCombine = SupplierQualityCombine;
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = SupplierQualityCombine;
}
