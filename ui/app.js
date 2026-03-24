const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const liveBtn = document.getElementById("liveBtn");
const replayBtn = document.getElementById("replayBtn");
const stopBtn = document.getElementById("stopBtn");
const taskCard = document.getElementById("taskCard");
const taskName = document.getElementById("taskName");
const taskResult = document.getElementById("taskResult");
const taskTime = document.getElementById("taskTime");
const flowCard = document.getElementById("flowCard");
const flowView = document.getElementById("flowView");
const mermaidCard = document.getElementById("mermaidCard");
const mermaidView = document.getElementById("mermaidView");
const stepsCard = document.getElementById("stepsCard");
const stepsTableBody = document.querySelector("#stepsTable tbody");

mermaid.initialize({ startOnLoad: false, theme: "dark" });

let lastTraceHash = null;
let liveInterval = null;
let mermaidCounter = 0;
let currentTrace = null;
let replayTimer = null;

// File input
fileInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  fileName.textContent = file.name;
  const text = await file.text();
  const trace = JSON.parse(text);
  currentTrace = trace;
  renderTrace(trace);
});

// Live mode toggle
liveBtn.addEventListener("click", () => {
  if (liveInterval) {
    clearInterval(liveInterval);
    liveInterval = null;
    liveBtn.textContent = "Live Mode: OFF";
    liveBtn.classList.remove("active");
    fileName.textContent = "";
  } else {
    stopReplay();
    liveBtn.textContent = "Live Mode: ON";
    liveBtn.classList.add("active");
    fileName.textContent = "Polling latest_trace.json...";
    liveInterval = setInterval(pollTrace, 800);
    pollTrace();
  }
});

// Replay
replayBtn.addEventListener("click", startReplay);
stopBtn.addEventListener("click", stopReplay);

async function pollTrace() {
  try {
    const res = await fetch("latest_trace.json?t=" + Date.now());
    if (!res.ok) return;
    const trace = await res.json();
    const hash = JSON.stringify(trace);
    if (hash !== lastTraceHash) {
      lastTraceHash = hash;
      currentTrace = trace;
      fileName.textContent = "Live \u2014 updated " + new Date().toLocaleTimeString();
      renderTrace(trace);
    }
  } catch (e) {
    // Waiting for trace file
  }
}

function startReplay() {
  if (!currentTrace || !currentTrace.steps || currentTrace.steps.length === 0) return;

  stopReplay();

  // Pause live mode during replay
  if (liveInterval) {
    clearInterval(liveInterval);
    liveInterval = null;
    liveBtn.textContent = "Live Mode: OFF";
    liveBtn.classList.remove("active");
  }

  replayBtn.style.display = "none";
  stopBtn.style.display = "inline-block";
  fileName.textContent = "Replaying...";

  const steps = currentTrace.steps;
  let idx = 0;

  // Show empty state first
  renderTrace({ ...currentTrace, steps: [], result: "running" });

  replayTimer = setInterval(() => {
    idx++;

    if (idx > steps.length) {
      stopReplay();
      renderTrace(currentTrace);
      fileName.textContent = "Replay complete";
      return;
    }

    const partialSteps = steps.slice(0, idx);
    const lastStep = partialSteps[partialSteps.length - 1];
    const isComplete = idx === steps.length;
    const result = isComplete ? currentTrace.result : "running";

    renderTrace({
      ...currentTrace,
      steps: partialSteps,
      result,
      finished_at: isComplete ? currentTrace.finished_at : "...",
    }, idx - 1);

  }, 400);
}

function stopReplay() {
  if (replayTimer) {
    clearInterval(replayTimer);
    replayTimer = null;
  }
  replayBtn.style.display = "inline-block";
  stopBtn.style.display = "none";
}

function renderTrace(trace, highlightIdx) {
  if (!replayTimer) currentTrace = trace;

  taskCard.style.display = "block";
  taskName.textContent = trace.task || "unknown";

  const result = trace.result || "running";
  taskResult.textContent = result;
  taskResult.className = "task-result result-" + result;

  const started = trace.started_at || "?";
  const finished = trace.finished_at || "?";
  taskTime.textContent = `${started}  \u2192  ${finished}`;

  const grouped = buildGrouped(trace.steps || []);
  renderFlow(grouped);
  renderMermaid(grouped);
  renderTimeline(trace.steps || []);
  renderSteps(trace.steps || [], highlightIdx);
}

function buildGrouped(steps) {
  const map = new Map();
  const order = [];

  for (const step of steps) {
    if (!map.has(step.id)) {
      map.set(step.id, {
        skill: step.skill,
        failCount: 0,
        finalStatus: step.status,
        isRecovery: step.id.includes("_recovery"),
      });
      order.push(step.id);
    }
    const item = map.get(step.id);
    if (step.status === "failed") item.failCount++;
    item.finalStatus = step.status;
  }

  return order.map(id => ({ id, ...map.get(id) }));
}

function renderFlow(grouped) {
  flowCard.style.display = "block";
  flowView.innerHTML = "";

  grouped.forEach((item, i) => {
    if (i > 0) {
      const arrow = document.createElement("span");
      arrow.className = "flow-arrow";
      arrow.textContent = item.isRecovery ? "\u21E2" : "\u2192";
      flowView.appendChild(arrow);
    }

    const node = document.createElement("span");
    let label = item.skill;

    if (item.failCount > 0 && item.finalStatus === "success") {
      label += ` (retry \u00D7${item.failCount})`;
    } else if (item.failCount > 0 && item.finalStatus === "failed") {
      label += ` (FAIL \u00D7${item.failCount})`;
    }

    node.textContent = label;

    let cls = "flow-node ";
    if (item.finalStatus === "running") cls += "running";
    else if (item.finalStatus === "success") cls += "success";
    else if (item.finalStatus === "failed") cls += "failed";
    else if (item.isRecovery) cls += "recovered";

    node.className = cls;
    flowView.appendChild(node);
  });
}

async function renderMermaid(grouped) {
  mermaidCard.style.display = "block";

  let lines = ["graph LR"];
  const nodeIds = [];

  grouped.forEach((item, i) => {
    const nid = `N${i}`;
    nodeIds.push(nid);

    let label = item.skill;
    if (item.failCount > 0 && item.finalStatus === "success") {
      label += `<br/>(retry x${item.failCount})`;
    } else if (item.failCount > 0 && item.finalStatus === "failed") {
      label += `<br/>(FAIL x${item.failCount})`;
    }

    lines.push(`    ${nid}["${label}"]`);

    if (i > 0) {
      const prev = nodeIds[i - 1];
      if (item.isRecovery) {
        lines.push(`    ${prev} -.->|fallback| ${nid}`);
      } else {
        lines.push(`    ${prev} --> ${nid}`);
      }
    }
  });

  lines.push("");
  grouped.forEach((item, i) => {
    const nid = `N${i}`;
    if (item.finalStatus === "running") {
      lines.push(`    style ${nid} fill:#1f6feb,stroke:#388bfd,color:#fff`);
    } else if (item.finalStatus === "success") {
      lines.push(`    style ${nid} fill:#238636,stroke:#3fb950,color:#fff`);
    } else if (item.finalStatus === "failed") {
      lines.push(`    style ${nid} fill:#da3633,stroke:#f85149,color:#fff`);
    }
  });

  const mermaidCode = lines.join("\n");

  try {
    mermaidCounter++;
    const id = "mermaidGraph" + mermaidCounter;
    const { svg } = await mermaid.render(id, mermaidCode);
    mermaidView.innerHTML = svg;
  } catch (e) {
    mermaidView.innerHTML = `<pre style="color:#8b949e">${mermaidCode}</pre>`;
  }
}

function renderTimeline(steps) {
  const timelineCard = document.getElementById("timelineCard");
  const timeline = document.getElementById("timeline");
  const timelineStats = document.getElementById("timelineStats");

  timelineCard.style.display = "block";
  timeline.innerHTML = "";
  timelineStats.innerHTML = "";

  const grouped = new Map();
  const order = [];

  for (const step of steps) {
    if (!grouped.has(step.id)) {
      grouped.set(step.id, { skill: step.skill, entries: [], finalStatus: "running", isRecovery: step.id.includes("_recovery") });
      order.push(step.id);
    }
    const g = grouped.get(step.id);
    g.entries.push(step);
    g.finalStatus = step.status;
  }

  const items = [];
  let totalDuration = 0;

  for (const id of order) {
    const g = grouped.get(id);
    const entries = g.entries;
    const first = entries[0];
    const last = entries[entries.length - 1];

    let duration;
    if (first.time_ms && last.time_ms) {
      duration = Math.max(last.time_ms - first.time_ms, 50);
    } else {
      duration = 500;
    }

    items.push({ skill: g.skill, status: g.finalStatus, duration, isRecovery: g.isRecovery });
    totalDuration += duration;
  }

  for (const item of items) {
    const pct = Math.max((item.duration / totalDuration) * 100, 5);
    const bar = document.createElement("div");

    let statusClass = "tl-" + item.status;
    if (item.isRecovery && item.status === "success") statusClass = "tl-recovered";

    bar.className = `timeline-bar ${statusClass}`;
    bar.style.width = `${pct}%`;

    const durText = (item.duration / 1000).toFixed(2);
    bar.textContent = `${item.skill} (${durText}s)`;
    bar.title = `${item.skill}: ${durText}s \u2014 ${item.status}`;

    timeline.appendChild(bar);
  }

  const totalSec = (totalDuration / 1000).toFixed(2);
  const statsHtml = items.map(item => {
    const durText = (item.duration / 1000).toFixed(2);
    const dotClass = item.isRecovery ? "recovered" : item.status;
    return `<span class="timeline-stat"><span class="stat-dot ${dotClass}"></span>${item.skill}: ${durText}s</span>`;
  }).join("");

  timelineStats.innerHTML = `<span class="timeline-stat">Total: ${totalSec}s</span>` + statsHtml;
}

function renderSteps(steps, highlightIdx) {
  stepsCard.style.display = "block";
  stepsTableBody.innerHTML = "";

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const tr = document.createElement("tr");
    tr.className = "row-" + (step.status || "");

    if (highlightIdx !== undefined && i === highlightIdx) {
      tr.classList.add("current-step");
    }

    tr.innerHTML = `
      <td>${step.id || ""}</td>
      <td>${step.skill || ""}</td>
      <td class="status-${step.status}">${step.status || ""}</td>
      <td>${step.attempt ?? ""}</td>
      <td>${step.reason || ""}</td>
      <td>${step.time || ""}</td>
    `;

    stepsTableBody.appendChild(tr);
  }

  // Auto-scroll to current step
  if (highlightIdx !== undefined) {
    const rows = stepsTableBody.querySelectorAll("tr");
    if (rows[highlightIdx]) {
      rows[highlightIdx].scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }
}
