/**
 * Tax Structure Watch — Sortable Tables
 *
 * Adds click-to-sort functionality to tables with class="sortable".
 * Handles numeric and text sorting automatically.
 */

function initSortableTables() {
  document.querySelectorAll("table.sortable").forEach((table) => {
    const headers = table.querySelectorAll("thead th");
    const tbody = table.querySelector("tbody");

    if (!headers.length || !tbody) return;

    headers.forEach((th, colIndex) => {
      th.addEventListener("click", () => {
        const isAsc = th.classList.contains("sort-asc");
        const direction = isAsc ? "desc" : "asc";

        // Clear all sort classes
        headers.forEach((h) => h.classList.remove("sort-asc", "sort-desc"));
        th.classList.add(`sort-${direction}`);

        const rows = Array.from(tbody.querySelectorAll("tr"));

        rows.sort((a, b) => {
          const aCell = a.children[colIndex];
          const bCell = b.children[colIndex];
          if (!aCell || !bCell) return 0;

          let aVal = aCell.textContent.trim();
          let bVal = bCell.textContent.trim();

          // Try numeric comparison (strip %, $, commas)
          const aNum = parseFloat(aVal.replace(/[$,%]/g, "").replace(/,/g, ""));
          const bNum = parseFloat(bVal.replace(/[$,%]/g, "").replace(/,/g, ""));

          let result;
          if (!isNaN(aNum) && !isNaN(bNum)) {
            result = aNum - bNum;
          } else {
            result = aVal.localeCompare(bVal, undefined, { sensitivity: "base" });
          }

          return direction === "asc" ? result : -result;
        });

        rows.forEach((row) => tbody.appendChild(row));
      });
    });
  });
}

document.addEventListener("DOMContentLoaded", initSortableTables);

// Re-initialize on MkDocs instant navigation
if (typeof document$ !== "undefined") {
  document$.subscribe(initSortableTables);
}
