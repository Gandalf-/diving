(function () {
  'use strict';

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  function renderTotals(totals) {
    const container = document.getElementById('totals');
    if (!container || !totals) return;

    let html = '';
    for (const [key, value] of Object.entries(totals)) {
      html += `
        <div class="total-item">
            <div class="value">${value}</div>
            <div class="label">${key}</div>
        </div>
        `;
    }
    container.innerHTML = html;
  }

  function renderRecords(records) {
    const container = document.getElementById('records');
    if (!container || !records) return;

    let html = '';
    for (const [key, record] of Object.entries(records)) {
      const value = record.value + (record.unit ? ' ' + record.unit : '');
      const context = record.dive
        ? `${record.dive}<br>${formatDate(record.date)}`
        : formatDate(record.date);

      const cardContent = `
        <div class="label">${key}</div>
        <div class="value">${value}</div>
        <div class="context">${context}</div>
        `;

      if (record.link) {
        html += `<a href="${record.link}" class="record-card record-link">${cardContent}</a>`;
      } else {
        html += `<div class="record-card">${cardContent}</div>`;
      }
    }
    container.innerHTML = html;
  }

  function renderBarChart(containerId, data, color) {
    const container = document.getElementById(containerId);
    if (!container || !data || data.length === 0) {
      if (container) container.innerHTML = '<p>No data available</p>';
      return;
    }

    // Extract values
    const values = data.map((d) => d[2]);
    const maxValue = Math.max(...values);

    // Build simple bar chart using divs
    let html = '<div class="bar-chart">';
    for (let i = 0; i < data.length; i++) {
      const pct = maxValue > 0 ? (values[i] / maxValue) * 100 : 0;
      const label = `${data[i][0]}–${data[i][1]}`;
      html += `
        <div class="bar-row">
            <div class="bar-label">${label}</div>
            <div class="bar-container">
                <div class="bar" style="width: ${pct}%; background: ${color};"></div>
            </div>
            <div class="bar-value">${values[i]}</div>
        </div>
        `;
    }
    html += '</div>';

    container.innerHTML = html;
  }

  function renderLocations(locations) {
    const container = document.getElementById('locations');
    if (!container || !locations) return;

    // Sort by dive count descending
    const sorted = Object.entries(locations).sort((a, b) => b[1].dives - a[1].dives);

    let html = `
      <thead>
          <tr>
              <th>Region</th>
              <th>Dives</th>
              <th>Avg Depth (ft)</th>
              <th>Avg Temp (°F)</th>
              <th>Bottom Time (hrs)</th>
          </tr>
      </thead>
      <tbody>
      `;

    for (const [region, stats] of sorted) {
      html += `
        <tr>
            <td>${region}</td>
            <td>${stats.dives}</td>
            <td>${stats.avg_depth}</td>
            <td>${stats.avg_temp}</td>
            <td>${stats.bottom_time}</td>
        </tr>
        `;
    }

    html += '</tbody>';
    container.innerHTML = html;
  }

  function init() {
    if (typeof stats_data === 'undefined') {
      console.error('stats_data not loaded');
      return;
    }

    renderTotals(stats_data.totals);
    renderRecords(stats_data.records);
    renderBarChart('depth-chart', stats_data.distributions.depth, '#4a90d9');
    renderBarChart('duration-chart', stats_data.distributions.duration, '#5cb85c');
    renderBarChart('temp-chart', stats_data.distributions.temperature, '#d9534f');
    renderBarChart('air-chart', stats_data.distributions.air, '#f0ad4e');
    renderBarChart('sac-chart', stats_data.distributions.sac, '#bf46ca');
    renderBarChart('end-chart', stats_data.distributions.end, '#f0ad4e');
    renderBarChart('start-chart', stats_data.distributions.start, '#f0ad4e');
    renderLocations(stats_data.locations);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
