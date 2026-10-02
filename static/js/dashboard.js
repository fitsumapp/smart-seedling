/**
 * Smart Agriculture Dashboard Client Logic
 * Handles real-time Chart.js rendering, live polling, and smooth visual flashes on incoming telemetry.
 */

document.addEventListener('DOMContentLoaded', () => {
    let telemetryChart = null;
    let distributionChart = null;
    let trendsChart = null;

    let selectedDeviceId = document.getElementById('deviceSelector')?.value || '';
    let selectedTimeRange = 'today';
    let lastKnownTemp = null;
    let lastKnownMoisture = null;
    let secondsSinceLastPacket = 0;

    // 1. Initialize Main Telemetry Line Chart
    const ctxTelemetry = document.getElementById('telemetryChart')?.getContext('2d');
    if (ctxTelemetry) {
        const gradientMoisture = ctxTelemetry.createLinearGradient(0, 0, 0, 240);
        gradientMoisture.addColorStop(0, 'rgba(82, 196, 122, 0.45)');
        gradientMoisture.addColorStop(1, 'rgba(82, 196, 122, 0.03)');

        telemetryChart = new Chart(ctxTelemetry, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Soil Moisture (%)',
                        data: [],
                        borderColor: '#0c3b20',
                        backgroundColor: gradientMoisture,
                        borderWidth: 2.8,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 2,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#0c3b20',
                        pointBorderColor: '#ffffff',
                        yAxisID: 'yMoisture',
                    },
                    {
                        label: 'Soil Temperature (°C)',
                        data: [],
                        borderColor: '#22c55e',
                        backgroundColor: 'transparent',
                        borderWidth: 2.2,
                        borderDash: [5, 4],
                        fill: false,
                        tension: 0.35,
                        pointRadius: 2,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#22c55e',
                        pointBorderColor: '#ffffff',
                        yAxisID: 'yTemp',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400 },
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            boxWidth: 12,
                            font: { family: 'Plus Jakarta Sans', size: 11, weight: '700' },
                            color: '#1f2937'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0c3b20',
                        titleFont: { family: 'Outfit', size: 12, weight: '700' },
                        bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                        padding: 10,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: '#6b7280', maxTicksLimit: 12 }
                    },
                    yMoisture: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: '#0c3b20', stepSize: 20 },
                        title: { display: true, text: 'Soil Moisture (%)', font: { size: 11, weight: 'bold' }, color: '#0c3b20' }
                    },
                    yTemp: {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: 45,
                        grid: { display: false },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: '#22c55e', stepSize: 10 },
                        title: { display: true, text: 'Temp (°C)', font: { size: 11, weight: 'bold' }, color: '#22c55e' }
                    }
                }
            }
        });
    }

    // 2. Initialize Seedling Distribution Donut Chart
    const ctxDonut = document.getElementById('distributionChart')?.getContext('2d');
    if (ctxDonut) {
        distributionChart = new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: ['Germinating', 'Growing', 'Ready for Transplant'],
                datasets: [{
                    data: [40, 80, 30],
                    backgroundColor: ['#0c3b20', '#22c55e', '#86efac'],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0c3b20',
                        cornerRadius: 6,
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${context.raw} Plants`;
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Initialize Weather & Irrigation Trends Chart
    const ctxTrends = document.getElementById('trendsChart')?.getContext('2d');
    if (ctxTrends) {
        trendsChart = new Chart(ctxTrends, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Soil Temperature (°C)',
                        data: [],
                        borderColor: '#0c3b20',
                        borderWidth: 2,
                        tension: 0.35,
                        pointRadius: 0,
                        fill: false,
                    },
                    {
                        label: 'Irrigation Pump Activity (%)',
                        data: [],
                        borderColor: '#22c55e',
                        borderWidth: 2,
                        borderDash: [5, 4],
                        tension: 0.1,
                        pointRadius: 0,
                        fill: false,
                    },
                    {
                        label: 'Cooling Fan Activity (%)',
                        data: [],
                        borderColor: '#0284c7',
                        borderWidth: 2,
                        borderDash: [2, 2],
                        tension: 0.1,
                        pointRadius: 0,
                        fill: false,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { backgroundColor: '#0c3b20', cornerRadius: 6 }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 9 }, color: '#9ca3af', maxTicksLimit: 10 } },
                    y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 9 }, color: '#9ca3af' } }
                }
            }
        });
    }

    // 4. Fetch and update telemetry data
    async function fetchDashboardTelemetry() {
        try {
            const url = `/dashboard/api/telemetry/?device_id=${encodeURIComponent(selectedDeviceId)}&time_range=${encodeURIComponent(selectedTimeRange)}&_t=${Date.now()}`;
            const response = await fetch(url);
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            // Elements
            const tempEl = document.getElementById('liveTemp');
            const timeEl = document.getElementById('liveTime');
            const moistureTextEl = document.getElementById('liveMoistureText');
            const airClimateTextEl = document.getElementById('liveAirClimateText');
            const pumpTextEl = document.getElementById('livePumpText');
            const fanTextEl = document.getElementById('liveFanText');
            const deviceStatusBadge = document.getElementById('liveDeviceStatus');
            const livePulseIndicator = document.getElementById('livePulseIndicator');

            const currentTemp = data.latest.temperature;
            const currentMoisture = data.latest.moisture;

            // Trigger visual flash if new values arrived
            if (lastKnownTemp !== null && (lastKnownTemp !== currentTemp || lastKnownMoisture !== currentMoisture)) {
                secondsSinceLastPacket = 0;
                if (tempEl) {
                    tempEl.style.transform = 'scale(1.08)';
                    tempEl.style.boxShadow = '0 0 15px rgba(34, 197, 94, 0.8)';
                    setTimeout(() => {
                        tempEl.style.transform = 'scale(1)';
                        tempEl.style.boxShadow = '';
                    }, 400);
                }
            }

            lastKnownTemp = currentTemp;
            lastKnownMoisture = currentMoisture;

            if (tempEl) tempEl.textContent = `${currentTemp.toFixed(1)}°c`;
            if (timeEl) timeEl.textContent = `${data.latest.timestamp} (${secondsSinceLastPacket}s ago)`;
            if (moistureTextEl) moistureTextEl.textContent = `Soil Moisture: ${currentMoisture.toFixed(1)}%`;
            
            if (airClimateTextEl && data.latest.air_temperature !== undefined) {
                airClimateTextEl.textContent = `Ambient Air: ${data.latest.air_temperature.toFixed(1)}°C • ${data.latest.air_humidity.toFixed(1)}%`;
            }

            if (pumpTextEl) {
                if (data.latest.pump_status) {
                    pumpTextEl.textContent = 'Pump: ACTIVE (Irrigating)';
                    pumpTextEl.className = 'text-success fw-bold';
                } else {
                    pumpTextEl.textContent = 'Pump: IDLE / OFF';
                    pumpTextEl.className = 'text-muted';
                }
            }

            if (fanTextEl) {
                if (data.latest.fan_status) {
                    fanTextEl.textContent = 'Fan: ACTIVE (Cooling)';
                    fanTextEl.className = 'text-primary fw-bold';
                } else {
                    fanTextEl.textContent = 'Fan: IDLE / OFF';
                    fanTextEl.className = 'text-muted';
                }
            }

            if (deviceStatusBadge) {
                deviceStatusBadge.textContent = data.device.is_online ? 'ESP32/ESP8266 Live Connected' : 'Device Offline';
                deviceStatusBadge.className = data.device.is_online ? 'badge bg-success' : 'badge bg-secondary';
            }

            if (livePulseIndicator) {
                livePulseIndicator.className = data.device.is_online ? 'pulse-dot bg-success' : 'pulse-dot bg-secondary';
            }

            // Update Top 4 Metric Cards
            const card1 = document.getElementById('metricNurseries');
            const card2 = document.getElementById('metricActiveDevices');
            const card3 = document.getElementById('metricSeedlings');
            const card4 = document.getElementById('metricAlerts');

            if (card1) card1.textContent = data.metrics.total_nurseries;
            if (card2) card2.textContent = data.metrics.active_devices;
            if (card3) card3.textContent = data.metrics.total_seedlings;
            if (card4) card4.textContent = data.metrics.active_alerts;

            // Update Donut Center Number
            const donutCenterEl = document.getElementById('donutCenterNumber');
            if (donutCenterEl) {
                donutCenterEl.textContent = data.metrics.total_seedlings.toLocaleString();
            }

            // Update Farmland Health Percentage
            const healthPctEl = document.getElementById('healthPercentage');
            if (healthPctEl) {
                healthPctEl.textContent = `${data.metrics.health_percentage}%`;
            }

            // Update Segmented Equalizer Bars
            updateEqualizerBars(data.metrics.health_percentage);

            // Update Charts
            if (telemetryChart && data.charts.labels.length > 0) {
                telemetryChart.data.labels = data.charts.labels;
                telemetryChart.data.datasets[0].data = data.charts.moisture;
                telemetryChart.data.datasets[1].data = data.charts.temperature;
                telemetryChart.update('none'); // Fast update without lag
            }

            if (distributionChart && data.charts.batch_distribution) {
                distributionChart.data.labels = data.charts.batch_distribution.labels;
                distributionChart.data.datasets[0].data = data.charts.batch_distribution.data;
                distributionChart.update('none');
            }

            if (trendsChart && data.charts.labels.length > 0) {
                trendsChart.data.labels = data.charts.labels;
                trendsChart.data.datasets[0].data = data.charts.temperature;
                trendsChart.data.datasets[1].data = data.charts.pump_activity;
                if (trendsChart.data.datasets.length > 2 && data.charts.fan_activity) {
                    trendsChart.data.datasets[2].data = data.charts.fan_activity;
                }
                trendsChart.update('none');
            }

        } catch (err) {
            console.error('Error fetching dashboard telemetry:', err);
        }
    }

    // 5. Update Segmented Bars Helper
    function updateEqualizerBars(healthPercentage) {
        const barsContainer = document.getElementById('segmentedBars');
        if (!barsContainer) return;

        const totalBars = 16;
        const activeCount = Math.round((healthPercentage / 100) * totalBars);

        barsContainer.innerHTML = '';
        for (let i = 0; i < totalBars; i++) {
            const bar = document.createElement('div');
            bar.className = 'segment-bar';
            
            if (i < activeCount) {
                if (i >= totalBars - 3) {
                    bar.classList.add('active-light');
                } else {
                    bar.classList.add('active-bright');
                }
            } else {
                bar.classList.add('inactive');
            }
            barsContainer.appendChild(bar);
        }
    }

    // 6. Simulate Telemetry Trigger
    const btnSimulate = document.getElementById('btnSimulateFeed');
    if (btnSimulate) {
        btnSimulate.addEventListener('click', async () => {
            btnSimulate.classList.add('disabled');
            btnSimulate.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Injecting...';
            try {
                const res = await fetch('/dashboard/api/simulate/', { method: 'POST' });
                if (res.ok) {
                    await fetchDashboardTelemetry();
                }
            } finally {
                btnSimulate.classList.remove('disabled');
                btnSimulate.innerHTML = '<span class="material-symbols-outlined fs-6">bolt</span> Test Live Feed';
            }
        });
    }

    // 7. Event Listeners for Filters
    const deviceSelect = document.getElementById('deviceSelector');
    if (deviceSelect) {
        deviceSelect.addEventListener('change', (e) => {
            selectedDeviceId = e.target.value;
            fetchDashboardTelemetry();
        });
    }

    const timeFilterButtons = document.querySelectorAll('[data-time-range]');
    timeFilterButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            timeFilterButtons.forEach(b => b.classList.remove('active', 'btn-dark'));
            btn.classList.add('active', 'btn-dark');
            selectedTimeRange = btn.getAttribute('data-time-range');
            fetchDashboardTelemetry();
        });
    });

    // 8. Timers: Increment local counter and poll backend every 1.5 seconds
    setInterval(() => {
        secondsSinceLastPacket += 1;
        const timeEl = document.getElementById('liveTime');
        if (timeEl && lastKnownTemp !== null) {
            timeEl.textContent = `Live Telemetry (${secondsSinceLastPacket}s ago)`;
        }
    }, 1000);

    fetchDashboardTelemetry();
    setInterval(fetchDashboardTelemetry, 1000); // Fast live polling every 1 second

});
