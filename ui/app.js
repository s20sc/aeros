const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
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

fileInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  fileName.textContent = file.name;
  const text = await file.text();
  const trace = JSON.parse(text);
  renderTrace(trace);
});

function renderTrace(trace) {
  // Task info
  taskCard.style.display = "block";
  taskName.textContent = trace.task || "unknown";

  const result = trace.result || "running";
  taskResult.textContent = result;
  taskResult.className = "task-result result-" + result;

  const started = trace.started_at || "?";
  const finished = trace.finished_at || "?";
  taskTime.textContent = `${started}  \u2192  ${finished}`;

  // Flow view
  const grouped = buildGrouped(trace.steps || []);
  renderFlow(grouped);

  // Mermaid
  renderMermaid(grouped);

  // Steps table
  renderSteps(trace.steps || []);
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
    if (item.finalStatus === "success") cls += "success";
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

  // Styles
  lines.push("");
  grouped.forEach((item, i) => {
    const nid = `N${i}`;
    if (item.finalStatus === "success") {
      lines.push(`    style ${nid} fill:#238636,stroke:#3fb950,color:#fff`);
    } else if (item.finalStatus === "failed") {
      lines.push(`    style ${nid} fill:#da3633,stroke:#f85149,color:#fff`);
    } else if (item.isRecovery) {
      lines.push(`    style ${nid} fill:#d29922,stroke:#e3b341,color:#fff`);
    }
  });

  const mermaidCode = lines.join("\n");

  try {
    const { svg } = await mermaid.render("mermaidGraph", mermaidCode);
    mermaidView.innerHTML = svg;
  } catch (e) {
    mermaidView.innerHTML = `<pre>${mermaidCode}</pre>`;
  }
}

function renderSteps(steps) {
  stepsCard.style.display = "block";
  stepsTableBody.innerHTML = "";

  for (const step of steps) {
    const tr = document.createElement("tr");
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
}
