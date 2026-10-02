/**
 * Smart Agriculture Dashboard Client Logic
 * Handles real-time Chart.js rendering, live polling, and smooth visual flashes on incoming telemetry.
 */

document.addEventListener('DOMContentLoaded', () => {
    let telemetryChart = null;
    let ambientChart = null;
    let distributionChart = null;
    let trendsChart = null;

    let selectedDeviceId = document.getElementById('deviceSelector')?.value || '';
    let selectedTimeRange = 'today';
    let lastKnownSoilTemp = null;
    let lastKnownAirTemp = null;
    let lastKnownMoisture = null;
    let secondsSinceLastPacket = 0;

    // 1. Initialize Main Soil Telemetry Line Chart (Moisture & Soil Temp)
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
                        title: { display: true, text: 'Soil Temp (°C)', font: { size: 11, weight: 'bold' }, color: '#22c55e' }
                    }
                }
            }
        });
    }

    // 2. Initialize Ambient Greenhouse Climate Chart (DHT22 Air Temp & Humidity)
    const ctxAmbient = document.getElementById('ambientClimateChart')?.getContext('2d');
    if (ctxAmbient) {
        const gradientHumidity = ctxAmbient.createLinearGradient(0, 0, 0, 240);
        gradientHumidity.addColorStop(0, 'rgba(59, 130, 246, 0.40)');
        gradientHumidity.addColorStop(1, 'rgba(59, 130, 246, 0.02)');

        ambientChart = new Chart(ctxAmbient, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Relative Humidity (%)',
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: gradientHumidity,
                        borderWidth: 2.6,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 2,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#2563eb',
                        pointBorderColor: '#ffffff',
                        yAxisID: 'yHum',
                    },
                    {
                        label: 'Ambient Air Temperature (°C)',
                        data: [],
                        borderColor: '#0284c7',
                        backgroundColor: 'transparent',
                        borderWidth: 2.6,
                        fill: false,
                        tension: 0.35,
                        pointRadius: 2,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#0284c7',
                        pointBorderColor: '#ffffff',
                        yAxisID: 'yAirTemp',
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
                        backgroundColor: '#0f172a',
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
                    yHum: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: '#2563eb', stepSize: 20 },
                        title: { display: true, text: 'Air Humidity (%)', font: { size: 11, weight: 'bold' }, color: '#2563eb' }
                    },
                    yAirTemp: {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: 50,
                        grid: { display: false },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: '#0284c7', stepSize: 10 },
                        title: { display: true, text: 'Air Temp (°C)', font: { size: 11, weight: 'bold' }, color: '#0284c7' }
                    }
                }
            }
        });
    }

    // 3. Initialize Seedling Distribution Donut Chart
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

    // 4. Initialize Actuation Timeline Chart (Pump & Fan Relays)
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
                        borderColor: '#10b981',
                        borderWidth: 2,
                        tension: 0.35,
                        pointRadius: 0,
                        fill: false,
                    },
                    {
                        label: 'Irrigation Pump Active (%)',
                        data: [],
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.15)',
                        borderWidth: 2,
                        borderDash: [4, 3],
                        tension: 0.1,
                        pointRadius: 0,
                        fill: true,
                    },
                    {
                        label: 'Cooling Fan Active (%)',
                        data: [],
                        borderColor: '#0284c7',
                        backgroundColor: 'rgba(2, 132, 199, 0.15)',
                        borderWidth: 2,
                        borderDash: [2, 2],
                        tension: 0.1,
                        pointRadius: 0,
                        fill: true,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: { boxWidth: 10, font: { size: 10 } }
                    },
                    tooltip: { backgroundColor: '#0c3b20', cornerRadius: 6 }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 9 }, color: '#9ca3af', maxTicksLimit: 12 } },
                    y: { grid: { color: 'rgba(0,0,0,0.04)' }, min: 0, max: 100, ticks: { font: { size: 9 }, color: '#9ca3af' } }
                }
            }
        });
    }

    // 5. Fetch and update telemetry data
    async function fetchDashboardTelemetry() {
        try {
            const url = `/dashboard/api/telemetry/?device_id=${encodeURIComponent(selectedDeviceId)}&time_range=${encodeURIComponent(selectedTimeRange)}&_t=${Date.now()}`;
            const response = await fetch(url);
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            // Elements
            const soilTempEl = document.getElementById('liveSoilTemp');
            const airTempEl = document.getElementById('liveAirTemp');
            const soilTempBadge = document.getElementById('liveSoilTempBadge');
            const airTempBadge = document.getElementById('liveAirTempBadge');

            const timeEl = document.getElementById('liveTime');
            const moistureTextEl = document.getElementById('liveMoistureText');
            const soilTempTextEl = document.getElementById('liveSoilTempText');
            const airClimateTextEl = document.getElementById('liveAirClimateText');
            const pumpTextEl = document.getElementById('livePumpText');
            const fanTextEl = document.getElementById('liveFanText');
            const deviceStatusBadge = document.getElementById('liveDeviceStatus');
            const livePulseIndicator = document.getElementById('livePulseIndicator');

            const currentSoilTemp = data.latest.temperature;
            const currentAirTemp = data.latest.air_temperature !== undefined ? data.latest.air_temperature : (currentSoilTemp + 1.2);
            const currentAirHum = data.latest.air_humidity !== undefined ? data.latest.air_humidity : 65.0;
            const currentMoisture = data.latest.moisture;

            // Trigger visual flash if new values arrived
            if (lastKnownSoilTemp !== null && (lastKnownSoilTemp !== currentSoilTemp || lastKnownMoisture !== currentMoisture)) {
                secondsSinceLastPacket = 0;
                if (soilTempBadge) {
                    soilTempBadge.style.transform = 'scale(1.08)';
                    soilTempBadge.style.boxShadow = '0 0 16px rgba(34, 197, 94, 0.9)';
                    setTimeout(() => {
                        soilTempBadge.style.transform = 'scale(1)';
                        soilTempBadge.style.boxShadow = '';
                    }, 400);
                }
            }

            if (lastKnownAirTemp !== null && lastKnownAirTemp !== currentAirTemp) {
                if (airTempBadge) {
                    airTempBadge.style.transform = 'scale(1.08)';
                    airTempBadge.style.boxShadow = '0 0 16px rgba(14, 165, 233, 0.9)';
                    setTimeout(() => {
                        airTempBadge.style.transform = 'scale(1)';
                        airTempBadge.style.boxShadow = '';
                    }, 400);
                }
            }

            lastKnownSoilTemp = currentSoilTemp;
            lastKnownAirTemp = currentAirTemp;
            lastKnownMoisture = currentMoisture;

            if (soilTempEl) soilTempEl.textContent = `${currentSoilTemp.toFixed(1)}°C`;
            if (airTempEl) airTempEl.textContent = `${currentAirTemp.toFixed(1)}°C`;

            if (timeEl) timeEl.textContent = `${data.latest.timestamp} (${secondsSinceLastPacket}s ago)`;
            if (moistureTextEl) moistureTextEl.textContent = `Soil Moisture: ${currentMoisture.toFixed(1)}%`;
            if (soilTempTextEl) soilTempTextEl.textContent = `Soil Temp: ${currentSoilTemp.toFixed(1)}°C`;
            
            if (airClimateTextEl) {
                airClimateTextEl.textContent = `Ambient Air: ${currentAirTemp.toFixed(1)}°C • ${currentAirHum.toFixed(1)}%`;
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
                telemetryChart.update('none');
            }

            if (ambientChart && data.charts.labels.length > 0) {
                ambientChart.data.labels = data.charts.labels;
                ambientChart.data.datasets[0].data = data.charts.air_humidity;
                ambientChart.data.datasets[1].data = data.charts.air_temperature;
                ambientChart.update('none');
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

    // 6. Update Segmented Bars Helper
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

    // 7. Simulate Telemetry Trigger
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

    // 8. Event Listeners for Filters
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

    // 9. Timers: Increment local counter and poll backend every 1 second
    setInterval(() => {
        secondsSinceLastPacket += 1;
        const timeEl = document.getElementById('liveTime');
        if (timeEl && lastKnownSoilTemp !== null) {
            timeEl.textContent = `Live Telemetry (${secondsSinceLastPacket}s ago)`;
        }
    }, 1000);

    fetchDashboardTelemetry();
    setInterval(fetchDashboardTelemetry, 1000); // Fast live polling every 1 second

});
