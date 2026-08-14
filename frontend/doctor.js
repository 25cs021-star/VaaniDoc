// VaaniDoc - Doctor Dashboard logic

const API_BASE = "https://vaanidoc-vwtv.onrender.com";
const POLL_INTERVAL_MS = 3000;

const sessionListEl = document.getElementById("sessionList");
const clockDisplay = document.getElementById("clockDisplay");
const liveStatus = document.getElementById("liveStatus");

const patientId = document.getElementById("patientId");
const sessionTiming = document.getElementById("sessionTiming");
const languageBadge = document.getElementById("languageBadge");
const infoEntryTime = document.getElementById("infoEntryTime");
const infoLanguage = document.getElementById("infoLanguage");
const infoDuration = document.getElementById("infoDuration");
const infoSymptoms = document.getElementById("infoSymptoms");
const infoSeverity = document.getElementById("infoSeverity");
const infoCategory = document.getElementById("infoCategory");
const infoStatus = document.getElementById("infoStatus");
const infoSummary = document.getElementById("infoSummary");
const reviewButton = document.getElementById("reviewButton");
const endSessionButton = document.getElementById("endSessionButton");

let selectedSessionId = null;

// ---- Live clock -------------------------------------------------------
function updateClock() {
    if (!clockDisplay) return;
    clockDisplay.textContent = new Date().toLocaleString("en-IN", {
        weekday: "short", year: "numeric", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
}
updateClock();
setInterval(updateClock, 1000);

// ---- Session list -------------------------------------------------------
async function refreshSessionList() {
    try {
        const res = await fetch(`${API_BASE}/api/sessions`);
        if (!res.ok) throw new Error("Failed to fetch sessions");
        const sessions = await res.json();

        liveStatus.textContent = "● Live";
        liveStatus.classList.remove("status-offline");

        if (sessions.length === 0) {
            sessionListEl.innerHTML = `<p class="empty-state">No active sessions yet.</p>`;
            return;
        }

        sessionListEl.innerHTML = "";
        sessions.forEach((s) => {
            const item = document.createElement("button");
            item.className = "session-item" + (s.session_id === selectedSessionId ? " session-item-active" : "");
            item.innerHTML = `
                <div class="session-item-top">
                    <strong>${s.session_id}</strong>
                </div>
                <div class="session-item-bottom">
                    <span>${s.language}</span>
                    <span>${s.category}</span>
                </div>
                <div class="session-item-time">Entered ${new Date(s.created_at).toLocaleString("en-IN")}</div>
            `;
            item.addEventListener("click", () => selectSession(s.session_id));
            sessionListEl.appendChild(item);
        });

        // If nothing selected yet, auto-select the most recent (first) session
        if (!selectedSessionId && sessions.length > 0) {
            selectSession(sessions[0].session_id);
        }
    } catch (err) {
        liveStatus.textContent = "● Offline";
        liveStatus.classList.add("status-offline");
    }
}

// ---- Session detail -------------------------------------------------------
async function selectSession(sessionId) {
    selectedSessionId = sessionId;
    try {
        const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
        if (!res.ok) {
            // Session may have expired between list refresh and click
            selectedSessionId = null;
            resetDetailPanel("This session has expired or was deleted.");
            refreshSessionList();
            return;
        }
        const data = await res.json();
        renderDetail(data);
        refreshSessionList(); // to update highlighted state
    } catch (err) {
        resetDetailPanel("Could not load session details.");
    }
}

function renderDetail(data) {
    patientId.textContent = data.session_id;
    const entryTimeText = new Date(data.created_at).toLocaleString("en-IN", {
        weekday: "short", year: "numeric", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
    sessionTiming.textContent = `Submitted ${entryTimeText} · expires ${new Date(data.expires_at).toLocaleTimeString("en-IN")}`;
    languageBadge.textContent = data.language;
    infoEntryTime.textContent = entryTimeText;
    infoLanguage.textContent = data.language;
    infoDuration.textContent = data.duration;
    infoSymptoms.textContent = Array.isArray(data.symptoms) ? data.symptoms.join(", ") : data.symptoms;
    infoSeverity.textContent = data.severity;
    infoCategory.textContent = data.category;
    infoStatus.textContent = data.status;
    infoSummary.textContent = data.summary;

    reviewButton.disabled = false;
    endSessionButton.disabled = false;
}

function resetDetailPanel(message) {
    patientId.textContent = "No session selected";
    sessionTiming.textContent = "-";
    languageBadge.textContent = "-";
    infoEntryTime.textContent = "-";
    infoLanguage.textContent = "-";
    infoDuration.textContent = "-";
    infoSymptoms.textContent = "-";
    infoSeverity.textContent = "-";
    infoCategory.textContent = "-";
    infoStatus.textContent = "-";
    infoSummary.textContent = message || "Select a session from the left to view details.";
    reviewButton.disabled = true;
    endSessionButton.disabled = true;
}

// ---- Actions -------------------------------------------------------
reviewButton.addEventListener("click", async () => {
    if (!selectedSessionId) return;
    await fetch(`${API_BASE}/api/session/${selectedSessionId}/review`, { method: "POST" });
    selectSession(selectedSessionId);
});

endSessionButton.addEventListener("click", async () => {
    if (!selectedSessionId) return;
    if (!confirm("End this session and permanently delete the patient's intake data?")) return;
    await fetch(`${API_BASE}/api/session/${selectedSessionId}/end`, { method: "POST" });
    selectedSessionId = null;
    resetDetailPanel("Session ended and data deleted.");
    refreshSessionList();
});

// ---- Init -------------------------------------------------------
resetDetailPanel();
refreshSessionList();
setInterval(refreshSessionList, POLL_INTERVAL_MS);
