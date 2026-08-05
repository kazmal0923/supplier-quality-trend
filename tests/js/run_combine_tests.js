"use strict";

const {
  combineEntityMonths,
  labelCombinedSelection,
} = require("../../web/combine.js");

function assert(condition, message) {
  if (!condition) {
    console.error(`FAIL: ${message}`);
    process.exitCode = 1;
  } else {
    console.log(`ok: ${message}`);
  }
}

const janA = {
  targetMonth: "2026-01",
  returnQuantity: "1",
  shipmentQuantity: "100",
  defectiveRate: "0.01",
  statuses: [],
  warningCodes: [],
};
const janB = {
  targetMonth: "2026-01",
  returnQuantity: "3",
  shipmentQuantity: "100",
  defectiveRate: "0.03",
  statuses: [],
  warningCodes: [],
};
const missing = {
  targetMonth: "2026-02",
  returnQuantity: "0",
  shipmentQuantity: "0",
  defectiveRate: null,
  statuses: ["missing"],
  warningCodes: ["MISSING_MONTH"],
};

const combined = combineEntityMonths([
  {
    entityType: "supplier",
    displayName: "A",
    category: "国内仕入れ",
    supplierIds: ["17"],
    supplierNames: ["A"],
    months: [janA, missing],
  },
  {
    entityType: "supplier",
    displayName: "B",
    category: "海外仕入れ",
    supplierIds: ["176"],
    supplierNames: ["B"],
    months: [janB],
  },
]);

assert(combined !== null, "combined entity is created");
assert(combined.supplierIds.join(",") === "17,176", "supplier ids merged");
assert(combined.category.includes("国内仕入れ"), "keeps domestic category");
assert(combined.category.includes("海外仕入れ"), "keeps overseas category");

const january = combined.months.find((item) => item.targetMonth === "2026-01");
assert(january.returnQuantity === "4", "january returns summed");
assert(january.shipmentQuantity === "200", "january shipments summed");
assert(Number(january.defectiveRate) === 0.02, "january rate recalculated");

const february = combined.months.find((item) => item.targetMonth === "2026-02");
assert(february.statuses.includes("missing"), "all-missing month stays missing");

const label = labelCombinedSelection(combined, "supplier");
assert(label.includes("選択 2件"), "multi-select label");

const empty = combineEntityMonths([]);
assert(empty === null, "empty selection returns null");

if (process.exitCode) {
  process.exit(process.exitCode);
}
console.log("All combine.js checks passed");
