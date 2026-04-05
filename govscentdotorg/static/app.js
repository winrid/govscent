document.addEventListener('DOMContentLoaded', function () {
    initScoreChart();
    initFilterAutoSubmit();
});

function initScoreChart() {
    var dataEl = document.getElementById('chart-data');
    var canvasEl = document.getElementById('score-chart');
    if (!dataEl || !canvasEl) return;

    var data = JSON.parse(dataEl.textContent);
    canvasEl.height = 300;

    new Chart(canvasEl, {
        type: 'line',
        data: {
            labels: data.map(function (item) { return item.year; }),
            datasets: [{
                label: 'Avg On-Topic Score',
                data: data.map(function (item) { return item.score; }),
                borderColor: '#1B2A4A',
                backgroundColor: 'rgba(27, 42, 74, 0.05)',
                borderWidth: 2,
                pointBackgroundColor: '#C4453C',
                pointBorderColor: '#C4453C',
                pointRadius: 3,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1B2A4A',
                    titleFont: { family: 'Hanken Grotesk', size: 13 },
                    bodyFont: { family: 'Hanken Grotesk', size: 13 },
                    padding: 10,
                    cornerRadius: 6,
                    callbacks: {
                        title: function (items) {
                            var d = new Date(items[0].label);
                            return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                        },
                        label: function (item) {
                            return 'Score: ' + item.parsed.y.toFixed(1) + '/10';
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: 7,
                    max: 10,
                    ticks: {
                        font: { family: 'Hanken Grotesk', size: 12 },
                        color: '#8A8F9E',
                        stepSize: 0.5
                    },
                    grid: { color: '#E2DFD8' }
                },
                x: {
                    ticks: {
                        font: { family: 'Hanken Grotesk', size: 11 },
                        color: '#8A8F9E',
                        maxRotation: 45,
                        callback: function (val, index) {
                            var label = this.getLabelForValue(val);
                            var d = new Date(label);
                            if (isNaN(d)) return label;
                            return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                        }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

function initFilterAutoSubmit() {
    document.querySelectorAll('.filter-form select').forEach(function (select) {
        select.addEventListener('change', function () {
            this.closest('form').submit();
        });
    });
}
