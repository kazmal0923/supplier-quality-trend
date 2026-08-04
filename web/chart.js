"use strict";

let trendChart = null;

function formatChartRate(value) {
  return value === null ? "算出不可" : `${(Number(value) * 100).toFixed(2)}%`;
}

function chartStatusLabel(status) {
  return {
    missing: "欠損月",
    zero_shipment: "出荷数0",
    target_exceeded: "目標超過",
    abnormal: "100％以上",
    in_progress: "集計途中",
  }[status] ?? status;
}

window.renderTrendChart = function renderTrendChart(container, months) {
  if (!window.echarts) {
    container.textContent = "グラフライブラリを読み込めませんでした。";
    return;
  }
  if (!trendChart) trendChart = window.echarts.init(container);

  const values = months.map((month) =>
    month.defectiveRate === null ? null : Number(month.defectiveRate) * 100,
  );
  const abnormal = months.map((month) =>
    month.defectiveRate !== null && Number(month.defectiveRate) >= 1
      ? Number(month.defectiveRate) * 100
      : null,
  );
  const exceeded = months.map((month) =>
    month.defectiveRate !== null &&
    Number(month.defectiveRate) >= 0.01 &&
    Number(month.defectiveRate) < 1
      ? Number(month.defectiveRate) * 100
      : null,
  );
  const inProgress = months.map((month) =>
    month.statuses.includes("in_progress") && month.defectiveRate !== null
      ? Number(month.defectiveRate) * 100
      : null,
  );
  trendChart.setOption({
    animationDuration: 350,
    grid: { left: 60, right: 30, top: 45, bottom: 55 },
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const index = params[0]?.dataIndex ?? 0;
        const month = months[index];
        if (!month) return "";
        const states = month.statuses.length
          ? month.statuses.map(chartStatusLabel).join("、")
          : "正常";
        return [
          `<strong>${month.targetMonth}</strong>`,
          `返品数: ${month.returnQuantity}`,
          `出荷数: ${month.shipmentQuantity}`,
          `現行不良率: ${formatChartRate(month.defectiveRate)}`,
          `状態: ${states}`,
        ].join("<br>");
      },
    },
    xAxis: {
      type: "category",
      data: months.map((month) => month.targetMonth),
      axisLabel: { rotate: months.length > 15 ? 45 : 0 },
    },
    yAxis: {
      type: "value",
      name: "現行不良率（%）",
      axisLabel: { formatter: "{value}%" },
      min: 0,
    },
    series: [
      {
        name: "現行不良率",
        type: "line",
        data: values,
        connectNulls: false,
        symbolSize: 8,
        lineStyle: { width: 3 },
        markLine: {
          silent: true,
          symbol: "none",
          label: { formatter: "目標 1%" },
          data: [{ yAxis: 1 }],
        },
      },
      {
        name: "目標超過",
        type: "scatter",
        data: exceeded,
        symbolSize: 12,
        itemStyle: { color: "#b54708" },
      },
      {
        name: "100％以上",
        type: "scatter",
        data: abnormal,
        symbolSize: 14,
        itemStyle: { color: "#b42318" },
      },
      {
        name: "集計途中",
        type: "scatter",
        data: inProgress,
        symbol: "diamond",
        symbolSize: 16,
        itemStyle: { color: "#f2c94c", borderColor: "#172033", borderWidth: 1 },
      },
    ],
  });
};

window.resizeTrendChart = function resizeTrendChart() {
  trendChart?.resize();
};
