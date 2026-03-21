/**
 * Tax Structure Watch — Chart.js Integration
 *
 * Self-initializing module that finds canvas elements with data-chart-type
 * attributes, fetches JSON data, and renders Chart.js charts.
 *
 * Usage in Markdown:
 *   <canvas data-chart-type="pie"
 *           data-source="../assets/data/wi_profile.json"
 *           data-key="revenue_composition">
 *   </canvas>
 */

const CHART_DEFAULTS = {
  pie: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          padding: 16,
          usePointStyle: true,
          font: { size: 12 },
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.label || "";
            const value = context.parsed || 0;
            return `${label}: ${value}%`;
          },
        },
      },
    },
  },
  bar: {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Effective Tax Rate (%)",
          font: { size: 12 },
        },
        ticks: {
          callback: function (value) {
            return value + "%";
          },
        },
      },
      x: {
        ticks: {
          font: { size: 11 },
          maxRotation: 45,
        },
      },
    },
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          padding: 16,
          usePointStyle: true,
          font: { size: 12 },
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return `${context.dataset.label}: ${context.parsed.y}%`;
          },
        },
      },
    },
  },
  line: {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function (value) {
            return value.toLocaleString();
          },
        },
      },
    },
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          padding: 16,
          usePointStyle: true,
          font: { size: 12 },
        },
      },
    },
    elements: {
      line: { tension: 0.3 },
      point: { radius: 3 },
    },
  },
};

// Cache fetched JSON to avoid duplicate requests on the same page
const dataCache = new Map();

async function fetchData(url) {
  if (dataCache.has(url)) {
    return dataCache.get(url);
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }
  const data = await response.json();
  dataCache.set(url, data);
  return data;
}

function resolveKey(data, key) {
  return key.split(".").reduce((obj, k) => (obj && obj[k] !== undefined ? obj[k] : null), data);
}

async function initChart(canvas) {
  const chartType = canvas.dataset.chartType;
  const source = canvas.dataset.source;
  const key = canvas.dataset.key;

  if (!chartType || !source || !key) {
    console.warn("Chart element missing required data attributes:", canvas);
    return;
  }

  try {
    const data = await fetchData(source);
    const chartData = resolveKey(data, key);

    if (!chartData) {
      console.warn(`Key "${key}" not found in ${source}`);
      return;
    }

    const options = JSON.parse(JSON.stringify(CHART_DEFAULTS[chartType] || {}));

    // Override y-axis title if specified
    const yTitle = canvas.dataset.yTitle;
    if (yTitle && options.scales && options.scales.y) {
      options.scales.y.title = { display: true, text: yTitle, font: { size: 12 } };
    }

    new Chart(canvas, {
      type: chartType,
      data: chartData,
      options: options,
    });
  } catch (err) {
    console.error(`Error initializing chart:`, err);
    // Show fallback message
    const parent = canvas.parentElement;
    if (parent) {
      const msg = document.createElement("p");
      msg.style.cssText = "text-align:center;color:#999;font-style:italic;padding:2rem;";
      msg.textContent = "Chart data unavailable. Run the data pipeline to generate.";
      parent.replaceChild(msg, canvas);
    }
  }
}

// Use IntersectionObserver for lazy loading
function setupLazyCharts() {
  const canvases = document.querySelectorAll("canvas[data-chart-type]");

  if (!canvases.length) return;

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            initChart(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "200px" }
    );

    canvases.forEach((canvas) => observer.observe(canvas));
  } else {
    // Fallback: initialize all immediately
    canvases.forEach((canvas) => initChart(canvas));
  }
}

// Initialize on DOM ready and on MkDocs navigation (instant loading)
document.addEventListener("DOMContentLoaded", setupLazyCharts);

// MkDocs Material uses instant loading — re-init charts on navigation
if (typeof document$ !== "undefined") {
  document$.subscribe(setupLazyCharts);
}
