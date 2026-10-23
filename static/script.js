// Global state variables
let allSamples = [];
let fraudChart = null;          // Dashboard Doughnut Chart
let simDistributionChart = null; // Simulator Doughnut Chart
let comparisonChart = null;      // Metrics Comparison Bar Chart

// Simulator variables
let simTimer = null;
let simSpeed = 2.0; // seconds
let simModel = "dl";
let simStats = { total: 0, safe: 0, fraud: 0, blockchain: 0 };
let simActive = false;
let simulationRequestPending = false;
let simStartedAt = Date.now();
const simFeedBuffer = [];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}

// Page titles corresponding to tabs
const tabMeta = {
  dashboard: { title: "Dashboard Overview", subtitle: "Model predictions and ledger status for simulated sample transactions." },
  analyzer: { title: "Transaction Analyzer", subtitle: "Test the AI models with Kaggle credit card transactions and log to blockchain." },
  simulator: { title: "Sample Traffic Simulator", subtitle: "Replay perturbed dataset examples through the fraud classifier." },
  ledger: { title: "Fraud Audit Records", subtitle: "Ganache records and local simulation records are identified separately." },
  metrics: { title: "Model Performance Metrics", subtitle: "Evaluation results, confusion matrices, and model comparison." }
};

// On page load initialization
document.addEventListener("DOMContentLoaded", () => {
  generatePCAInputs();
  switchTab("dashboard", document.querySelector(".sidebar-menu .menu-item"));
  initChart();
  
  // Fetch initial data
  loadNetworkStatus();
  loadSampleTransactions();
  loadBlockchainLogs();
  
  // Refresh network stats periodically (every 10 seconds)
  setInterval(loadNetworkStatus, 10000);
});

// Tab Switching Mechanism
function switchTab(tabId, element) {
  // Stop simulator if switching away from simulator tab to save resources
  if (tabId !== "simulator" && simActive) {
    toggleSimulation();
  }

  // Update sidebar active state
  document.querySelectorAll(".sidebar-menu .menu-item").forEach(item => {
    item.classList.remove("active");
  });
  element.classList.add("active");
  
  // Toggle tab views
  document.querySelectorAll(".tab-view").forEach(view => {
    view.classList.remove("active");
  });
  document.getElementById(`tab-${tabId}`).classList.add("active");
  
  // Update Header text
  document.getElementById("page-title").innerText = tabMeta[tabId].title;
  document.getElementById("page-subtitle").innerText = tabMeta[tabId].subtitle;
  
  // Specific tab actions
  if (tabId === "ledger") {
    loadBlockchainLogs();
  }
  if (tabId === "dashboard") {
    loadNetworkStatus();
  }
  if (tabId === "simulator") {
    initSimChart();
  }
  if (tabId === "metrics") {
    loadNetworkStatus();
  }
}

// Generate Form Inputs for PCA V1 to V28
function generatePCAInputs() {
  const container = document.getElementById("pca-features-grid");
  if (!container) return;
  container.innerHTML = "";
  
  for (let i = 1; i <= 28; i++) {
    const group = document.createElement("div");
    group.className = "form-group";
    group.innerHTML = `
      <label for="input-V${i}">V${i}</label>
      <input type="number" step="any" id="input-V${i}" value="0.0">
    `;
    container.appendChild(group);
  }
}

// Accordion handler for PCA Features
function toggleFeaturesAccordion() {
  const content = document.getElementById("pca-features-grid");
  const icon = document.getElementById("accordion-icon");
  
  content.classList.toggle("open");
  if (content.classList.contains("open")) {
    icon.style.transform = "rotate(180deg)";
  } else {
    icon.style.transform = "rotate(0deg)";
  }
}

// Initialize Chart.js Pie Chart on Dashboard
function initChart() {
  if (typeof Chart === "undefined") return;
  const canvas = document.getElementById("fraudDistributionChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  
  if (fraudChart) {
    fraudChart.destroy();
  }
  
  fraudChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Safe Transactions", "Fraud Transactions"],
      datasets: [{
        data: [0, 0],
        backgroundColor: ["#10b981", "#ef4444"],
        borderColor: ["#0b0f19", "#0b0f19"],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#9ca3af',
            font: { family: 'Outfit', size: 12 }
          }
        }
      },
      cutout: "70%"
    }
  });
}

// Initialize Doughnut Chart for Live Simulator
function initSimChart() {
  if (typeof Chart === "undefined") return;
  const canvas = document.getElementById("simDistributionChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  
  if (simDistributionChart) {
    simDistributionChart.destroy();
  }
  
  simDistributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Safe", "Fraud"],
      datasets: [{
        data: [simStats.safe, simStats.fraud],
        backgroundColor: ["#10b981", "#ef4444"],
        borderColor: ["#0b0f19", "#0b0f19"],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#9ca3af',
            font: { family: 'Outfit', size: 12 }
          }
        }
      },
      cutout: "70%"
    }
  });
}

// Fetch Sample Transactions from Backend
function loadSampleTransactions() {
  fetch("/api/samples")
    .then(res => res.json())
    .then(data => {
      allSamples = data;
      renderSamplesTable(data);
    })
    .catch(err => console.error("Error loading samples:", err));
}

// Render samples in table
function renderSamplesTable(samples) {
  const tbody = document.getElementById("samples-list-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  if (samples.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center">No samples loaded. Try training the model first!</td></tr>`;
    return;
  }
  
  samples.forEach(sample => {
    const tr = document.createElement("tr");
    tr.id = `sample-row-${sample.id}`;
    
    const classBadge = sample.class === 1 
      ? `<span class="class-badge fraud">Fraud</span>` 
      : `<span class="class-badge normal">Safe</span>`;
      
    tr.innerHTML = `
      <td class="font-mono">#${sample.id}</td>
      <td>${classBadge}</td>
      <td class="font-mono">$${parseFloat(sample.features.Amount).toFixed(2)}</td>
      <td>
        <button class="btn btn-secondary btn-table" onclick="loadSampleToForm(${sample.id})">Load</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Filter/Search in Samples Table
function filterSamples() {
  const query = document.getElementById("sample-search").value.toLowerCase();
  
  const filtered = allSamples.filter(sample => {
    return sample.id.toString().includes(query) || 
           sample.features.Amount.toString().includes(query) ||
           (sample.class === 1 ? "fraud" : "safe").includes(query);
  });
  
  renderSamplesTable(filtered);
}

// Load selected sample parameters into form
function loadSampleToForm(sampleId) {
  const sample = allSamples.find(s => s.id === sampleId);
  if (!sample) return;
  
  // Load metadata/Time/Amount
  document.getElementById("input-Amount").value = sample.features.Amount;
  document.getElementById("input-Time").value = sample.features.Time;
  
  // Load V1-V28
  for (let i = 1; i <= 28; i++) {
    document.getElementById(`input-V${i}`).value = sample.features[`V${i}`];
  }
  
  // Force expand accordion to show loaded PCA features
  const content = document.getElementById("pca-features-grid");
  const icon = document.getElementById("accordion-icon");
  content.classList.add("open");
  icon.style.transform = "rotate(180deg)";
  
  // Highlight row in table
  document.querySelectorAll("#samples-list-body tr").forEach(row => {
    row.classList.remove("selected-row");
    row.style.backgroundColor = "";
  });
  const selectedRow = document.getElementById(`sample-row-${sampleId}`);
  if (selectedRow) {
    selectedRow.style.backgroundColor = "rgba(139, 92, 246, 0.15)";
  }
  
  console.log(`Loaded transaction #${sampleId}`);
}

// Submit Transaction to Model API
function analyzeTransaction(event) {
  event.preventDefault();
  
  const btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing AI Classifier...`;
  
  // Gather features
  const featuresObj = {
    Amount: parseFloat(document.getElementById("input-Amount").value),
    Time: parseFloat(document.getElementById("input-Time").value)
  };
  
  for (let i = 1; i <= 28; i++) {
    featuresObj[`V${i}`] = parseFloat(document.getElementById(`input-V${i}`).value);
  }
  
  const modelType = document.getElementById("select-model").value;
  const payload = {
    sender: document.getElementById("input-sender").value,
    receiver: document.getElementById("input-receiver").value,
    features: featuresObj,
    model_type: modelType
  };
  
  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-microchip"></i> Run Deep Learning Analysis`;
    
    if (data.status === "success") {
      // Increment local stats counters
      let checks = parseInt(localStorage.getItem("stats_total_checked") || 0);
      localStorage.setItem("stats_total_checked", checks + 1);
      if (data.prediction === "Fraud") {
        let frauds = parseInt(localStorage.getItem("stats_fraud_flagged") || 0);
        localStorage.setItem("stats_fraud_flagged", frauds + 1);
      }
      
      // Update dashboard stats counters
      updateDashboardStats(
        localStorage.getItem("stats_total_checked"),
        localStorage.getItem("stats_fraud_flagged")
      );
      
      displayResults(data);
    } else {
      alert("Error running prediction: " + data.message);
    }
  })
  .catch(err => {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-microchip"></i> Run Deep Learning Analysis`;
    console.error("Error analyzing:", err);
    alert("Connection error to server API.");
  });
}

// Display Prediction Results
function displayResults(data) {
  const card = document.getElementById("analysis-results-card");
  card.style.display = "block";
  
  // Verdict styling
  const badge = document.getElementById("verdict-badge");
  badge.innerText = data.prediction.toUpperCase();
  badge.className = "result-badge"; // Reset classes
  
  const probVal = data.probability * 100;
  document.getElementById("verdict-prob").innerText = `${probVal.toFixed(4)}%`;
  
  // Individual probabilities details
  document.getElementById("prob-val-dl").innerText = `${(data.dl_probability * 100).toFixed(4)}%`;
  document.getElementById("prob-val-rf").innerText = `${(data.rf_probability * 100).toFixed(4)}%`;
  
  const fill = document.getElementById("verdict-prob-fill");
  fill.style.width = `${Math.min(probVal, 100)}%`;
  fill.className = "gauge-bar-fill"; // Reset classes
  
  if (data.prediction === "Fraud") {
    badge.classList.add("fraud");
    fill.classList.add("fraud-gradient");
  } else {
    badge.classList.add("safe");
    fill.classList.add("safe-gradient");
  }
  
  // Blockchain registry logs receipt
  const bcReceipt = document.getElementById("blockchain-receipt");
  const simReceipt = document.getElementById("simulated-receipt");
  
  bcReceipt.style.display = "none";
  simReceipt.style.display = "none";
  
  if (data.prediction === "Fraud") {
    if (data.blockchain_logged && data.receipt) {
      bcReceipt.style.display = "block";
      document.getElementById("receipt-hash").innerText = data.receipt.tx_hash.substring(0, 18) + "...";
      document.getElementById("receipt-hash").title = data.receipt.tx_hash;
      document.getElementById("receipt-block").innerText = data.receipt.block_number;
      document.getElementById("receipt-gas").innerText = `${data.receipt.gas_used} units`;
      
      // Refresh explorer logs since we logged a new one
      loadBlockchainLogs();
      loadNetworkStatus();
    } else if (data.receipt) {
      // Local fallback is explicitly not shown as a blockchain receipt.
      simReceipt.style.display = "block";
      loadBlockchainLogs();
    } else {
      simReceipt.style.display = "block";
    }
  }
}

// Map blockchain status code to readable labels
function getStatusLabel(statusCode) {
  switch(parseInt(statusCode)) {
    case 0:
      return `<span class="status-badge status-flagged"><i class="fa-solid fa-triangle-exclamation"></i> Flagged</span>`;
    case 1:
      return `<span class="status-badge status-review"><i class="fa-solid fa-magnifying-glass"></i> Under Review</span>`;
    case 2:
      return `<span class="status-badge status-resolved"><i class="fa-solid fa-circle-check"></i> Resolved (Safe)</span>`;
    case 3:
      return `<span class="status-badge status-confirmed"><i class="fa-solid fa-ban"></i> Confirmed Fraud</span>`;
    default:
      return `<span class="status-badge status-flagged">Unknown</span>`;
  }
}

// Fetch Logged Transactions from Smart Contract
function loadBlockchainLogs() {
  fetch("/api/blockchain_logs")
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById("ledger-list-body");
      if (!tbody) return;
      tbody.innerHTML = "";
      
      document.getElementById("ledger-total-logs").innerText = data.length;
      document.getElementById("stats-blockchain-logs").innerText = data.length;
      
      if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center">No fraud logs found on the blockchain registry.</td></tr>`;
        return;
      }
      
      data.forEach(log => {
        const tr = document.createElement("tr");
        const date = new Date(log.timestamp * 1000).toLocaleString();
        
        tr.innerHTML = `
          <td class="font-mono">#${log.index}</td>
          <td>${date}</td>
          <td class="font-mono">$${parseFloat(log.amount).toFixed(2)}</td>
          <td>${escapeHtml(log.sender)}</td>
          <td>${escapeHtml(log.receiver)}</td>
          <td><span class="class-badge fraud">${escapeHtml(log.result)}</span></td>
          <td>${getStatusLabel(log.status)}<br><small>${log.ledger_mode === "ganache" ? "Ganache" : "Local simulation"}</small></td>
          <td>
            <button class="btn btn-secondary btn-table" onclick="openDisputeModal(${log.index}, ${log.status})">
              <i class="fa-solid fa-scale-balanced"></i> Resolve
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    })
    .catch(err => console.error("Error loading blockchain logs:", err));
}

// Dispute Manager Modal Control
function openDisputeModal(index, currentStatus) {
  document.getElementById("dispute-record-index").value = index;
  document.getElementById("select-dispute-status").value = currentStatus;
  document.getElementById("dispute-modal").style.display = "flex";
}

function closeDisputeModal() {
  document.getElementById("dispute-modal").style.display = "none";
}

function submitDisputeStatus() {
  const index = document.getElementById("dispute-record-index").value;
  const status = document.getElementById("select-dispute-status").value;
  
  closeDisputeModal();
  
  fetch("/api/update_status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index: index, status: status })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "success") {
      loadBlockchainLogs();
      loadNetworkStatus();
    } else {
      alert("Error updating status: " + data.message);
    }
  })
  .catch(err => {
    console.error("Error in status update request:", err);
    alert("Server communication error.");
  });
}

// Fetch Ganache Connection and Model performance metrics
function loadNetworkStatus() {
  fetch("/api/network_status")
    .then(res => res.json())
    .then(data => {
      // Sync indicator bars
      const netStatus = document.getElementById("net-status");
      const sidebarStatus = document.getElementById("sidebar-net-status");
      
      netStatus.innerText = data.status;
      document.getElementById("net-block").innerText = data.block_number;
      
      if (data.status === "Connected") {
        netStatus.style.color = "#10b981";
        document.getElementById("net-account").innerText = data.active_account.substring(0, 10) + "..." + data.active_account.substring(34);
        document.getElementById("net-account").title = data.active_account;
        document.getElementById("info-contract-address").innerText = data.contract_address;
        
        sidebarStatus.innerHTML = `<span class="pulse-dot green"></span><span>Node Connected</span>`;
      } else {
        netStatus.style.color = "#f59e0b"; // orange warning
        document.getElementById("net-account").innerText = "Simulation";
        document.getElementById("info-contract-address").innerText = "Simulation Sandbox Contract";
        
        sidebarStatus.innerHTML = `<span class="pulse-dot" style="background-color:#f59e0b"></span><span>Simulation Mode</span>`;
      }
      
      // Update statistics overview dashboard counters
      let totalChecks = localStorage.getItem("stats_total_checked") || 0;
      let totalFraud = localStorage.getItem("stats_fraud_flagged") || 0;
      
      updateDashboardStats(totalChecks, totalFraud);
      
      // Load model metrics to performance tab
      if (data.model_performance && data.model_performance.accuracy) {
        const stats = data.model_performance;
        
        // PyTorch Progress Bars
        document.getElementById("metric-recall").innerText = `${(stats.recall * 100).toFixed(2)}%`;
        document.getElementById("metric-accuracy").innerText = `${(stats.accuracy * 100).toFixed(2)}%`;
        document.getElementById("metric-f1").innerText = `${(stats.f1 * 100).toFixed(2)}%`;
        document.getElementById("metric-precision").innerText = `${(stats.precision * 100).toFixed(2)}%`;
        
        // Render RF Stats if available
        if (data.rf_performance && data.rf_performance.accuracy) {
          const rf = data.rf_performance;
          document.getElementById("rf-metric-recall").innerText = `${(rf.recall * 100).toFixed(2)}%`;
          document.getElementById("rf-metric-accuracy").innerText = `${(rf.accuracy * 100).toFixed(2)}%`;
          document.getElementById("rf-metric-f1").innerText = `${(rf.f1 * 100).toFixed(2)}%`;
          document.getElementById("rf-metric-precision").innerText = `${(rf.precision * 100).toFixed(2)}%`;
          
          document.getElementById("rf-fill-recall").style.width = `${(rf.recall * 100)}%`;
          document.getElementById("rf-fill-accuracy").style.width = `${(rf.accuracy * 100)}%`;
          document.getElementById("rf-fill-f1").style.width = `${(rf.f1 * 100)}%`;
          document.getElementById("rf-fill-precision").style.width = `${(rf.precision * 100)}%`;
          
          // Draw the side-by-side comparison chart
          drawComparisonChart(stats, rf);
        }
      }
    })
    .catch(err => console.error("Error loading network status:", err));
}

// Helper to update dashboard stats counters and charts
function updateDashboardStats(totalChecks, totalFraud) {
  const finalTotal = Number.isFinite(Number(totalChecks)) ? Number(totalChecks) : 0;
  const finalFraud = Number.isFinite(Number(totalFraud)) ? Number(totalFraud) : 0;
  
  document.getElementById("stats-total-checked").innerText = finalTotal.toLocaleString();
  document.getElementById("stats-fraud-flagged").innerText = finalFraud.toLocaleString();
  
  localStorage.setItem("stats_total_checked", finalTotal);
  localStorage.setItem("stats_fraud_flagged", finalFraud);
  
  // Update Pie chart data
  if (fraudChart) {
    const safeCount = finalTotal - finalFraud;
    fraudChart.data.datasets[0].data = [safeCount, finalFraud];
    fraudChart.update();
  }
}

// Draw Side-by-Side Model Comparison Chart (PyTorch vs RF)
function drawComparisonChart(dl, rf) {
  if (typeof Chart === "undefined") return;
  const canvas = document.getElementById("comparisonChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  
  if (comparisonChart) {
    comparisonChart.destroy();
  }
  
  comparisonChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Recall (Catch Fraud)', 'Accuracy', 'Precision', 'F1-Score'],
      datasets: [
        {
          label: 'PyTorch Neural Net (MLP)',
          data: [dl.recall * 100, dl.accuracy * 100, dl.precision * 100, dl.f1 * 100],
          backgroundColor: 'rgba(139, 92, 246, 0.65)', // Purple glass
          borderColor: '#8b5cf6',
          borderWidth: 1.5
        },
        {
          label: 'Random Forest Classifier',
          data: [rf.recall * 100, rf.accuracy * 100, rf.precision * 100, rf.f1 * 100],
          backgroundColor: 'rgba(59, 130, 246, 0.65)', // Blue glass
          borderColor: '#3b82f6',
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#9ca3af',
            font: { family: 'Outfit', size: 12 }
          }
        }
      },
      scales: {
        y: {
          max: 100,
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#9ca3af',
            callback: function(value) { return value + '%'; }
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#9ca3af'
          }
        }
      }
    }
  });
}

// ================= LIVE TRAFFIC SIMULATOR CORE LOGIC =================

function toggleSimulation() {
  const btn = document.getElementById("btn-toggle-sim");
  
  if (simActive) {
    // STOP SIMULATION
    simActive = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Start Simulation`;
    btn.className = "btn btn-primary";
    clearInterval(simTimer);
  } else {
    // START SIMULATION
    simActive = true;
    btn.innerHTML = `<i class="fa-solid fa-pause"></i> Pause Simulation`;
    btn.className = "btn btn-secondary";
    
    // Clear feed on start
    document.getElementById("sim-feed-list").innerHTML = "";
    
    // Reset live stats counters for this session
    simStats = { total: 0, safe: 0, fraud: 0, blockchain: 0 };
    simStartedAt = Date.now();
    updateSimStatsUI();
    
    // Run initial step
    runSimulationStep();
    // Schedule intervals
    simTimer = setInterval(runSimulationStep, simSpeed * 1000);
  }
}

function updateSimSpeed(value) {
  document.getElementById("sim-speed-val").innerText = parseFloat(value).toFixed(1) + "s";
  simSpeed = parseFloat(value);
  
  if (simActive) {
    // Restart timer with new speed
    clearInterval(simTimer);
    simTimer = setInterval(runSimulationStep, simSpeed * 1000);
  }
}

function updateSimModel(value) {
  simModel = value;
  console.log("Simulator classifier changed to: " + value);
}

// Fetch a synthetic transaction and run inference
function runSimulationStep() {
  if (simulationRequestPending) return;
  simulationRequestPending = true;
  (async () => {
    try {
      const sampleResponse = await fetch("/api/generate_simulated");
      const txData = await sampleResponse.json();
      if (!sampleResponse.ok || txData.status !== "success") throw new Error(txData.message || "Sample request failed");
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: txData.sender, receiver: txData.receiver, features: txData.features, model_type: simModel })
      });
      const predData = await response.json();
      if (!response.ok || predData.status !== "success") throw new Error(predData.message || "Prediction failed");
      simStats.total += 1;
      if (predData.prediction === "Fraud") {
        simStats.fraud += 1;
        if (predData.ledger_mode === "ganache") simStats.blockchain += 1;
      } else simStats.safe += 1;
      const totalChecks = parseInt(localStorage.getItem("stats_total_checked") || 0, 10);
      localStorage.setItem("stats_total_checked", totalChecks + 1);
      if (predData.prediction === "Fraud") {
        const frauds = parseInt(localStorage.getItem("stats_fraud_flagged") || 0, 10);
        localStorage.setItem("stats_fraud_flagged", frauds + 1);
      }
      updateSimStatsUI();
      renderSimFeedCard(txData, predData);
    } catch (err) {
      console.error("Error in simulator tick:", err);
    } finally {
      simulationRequestPending = false;
    }
  })();
}

// Update simulation statistics numbers and charts
function updateSimStatsUI() {
  document.getElementById("sim-stat-total").innerText = simStats.total;
  document.getElementById("sim-stat-safe").innerText = simStats.safe;
  document.getElementById("sim-stat-fraud").innerText = simStats.fraud;
  document.getElementById("sim-stat-blockchain").innerText = simStats.blockchain;
  const elapsedMinutes = Math.max((Date.now() - simStartedAt) / 60000, 1 / 60000);
  document.getElementById("sim-stat-rate").innerText = (simStats.total / elapsedMinutes).toFixed(1);
  
  if (simDistributionChart) {
    simDistributionChart.data.datasets[0].data = [simStats.safe, simStats.fraud];
    simDistributionChart.update();
  }
}

// Prepend transaction classification result card in the live feed list
function renderSimFeedCard(tx, pred) {
  const container = document.getElementById("sim-feed-list");
  if (!container) return;
  
  const card = document.createElement("div");
  const isFraud = pred.prediction === "Fraud";
  card.className = `sim-tx-card ${isFraud ? 'fraud-border' : 'safe-border'}`;
  
  const timestampStr = new Date().toLocaleTimeString();
  const txHash = pred.receipt?.tx_hash;
  const txHashSnippet = pred.ledger_mode === "ganache" && txHash
    ? `<span class="text-accent" title="${escapeHtml(txHash)}">Ganache tx: ${escapeHtml(txHash.substring(0, 14))}...</span>`
    : `<span class="text-muted">Local simulation (in-memory)</span>`;
    
  card.innerHTML = `
    <div class="sim-tx-header">
      <span class="tx-id">Tx Ref: #${Math.floor(100000 + Math.random() * 900000)}</span>
      <span class="tx-time text-muted"><i class="fa-regular fa-clock"></i> ${timestampStr}</span>
    </div>
    <div class="sim-tx-body">
      <div class="tx-details">
        <div class="tx-parties">${escapeHtml(tx.sender)} &rarr; ${escapeHtml(tx.receiver)}</div>
        <div class="tx-meta">Sample replay · ${(pred.probability * 100).toFixed(2)}% fraud probability · ${Number(pred.scoring_ms || 0).toFixed(1)} ms scoring · ${Number(pred.response_ms || 0).toFixed(1)} ms total API</div>
      </div>
      <div class="tx-amount" style="color: ${isFraud ? 'var(--color-fraud)' : 'var(--color-safe)'};">$${tx.features.Amount.toFixed(2)}</div>
    </div>
    <div class="sim-tx-footer">
      <span>Model Type: ${simModel.toUpperCase()}</span>
      <span>${isFraud ? txHashSnippet : '<span class="text-green"><i class="fa-regular fa-circle-check"></i> Passed Security</span>'}</span>
    </div>
  `;
  
  // Prepend to feed
  container.insertBefore(card, container.firstChild);
  
  // Truncate list if too long to keep DOM light
  if (container.children.length > 25) {
    container.removeChild(container.lastChild);
  }
}
