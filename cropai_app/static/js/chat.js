const historyEl = document.getElementById("chatHistory");
const input = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendChat");
const contextCard = document.getElementById("contextCard");
const chipsEl = document.getElementById("chips");

const chips = [
  "Why is my yield Medium?",
  "How to increase my yield?",
  "Best crop for my region?",
  "What does NDVI mean?",
  "Optimal fertilizer for Rice?",
  "What is water stress index?",
  "Compare crops for Rabi season",
  "How does Potassium affect yield?",
];

const WELCOME =
  "🌾 Hello! I am CropAI, your agricultural assistant. I can help you with:\n" +
  "→ Explaining your yield prediction results\n" +
  "→ Fertilizer and nutrient recommendations\n" +
  "→ Crop selection for your region and season\n" +
  "→ Soil health and pH management advice\n" +
  "→ Irrigation and water management tips\n" +
  "→ Explaining what each input feature means\n" +
  "→ Comparing different crops side by side\n\n" +
  "What would you like to know today?";

function loadHistory() {
  return JSON.parse(localStorage.getItem("chat_history") || "[]");
}
function saveHistory(h) {
  localStorage.setItem("chat_history", JSON.stringify(h));
}

function render() {
  const hist = loadHistory();
  historyEl.innerHTML = hist
    .map(
      (m) =>
        `<div class="chatBubble ${m.role === "user" ? "user" : "bot"}">${escapeHtml(m.content).replace(/\n/g, "<br/>")}<div><small>${m.time}</small></div></div>`,
    )
    .join("");
  historyEl.scrollTop = historyEl.scrollHeight;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function categoryChip(catRaw) {
  const c = String(catRaw || "").toLowerCase();
  if (c.includes("low")) return "🔴 LOW";
  if (c.includes("high")) return "🟢 HIGH";
  return "🟡 MEDIUM";
}

function renderContext() {
  const ctx = JSON.parse(localStorage.getItem("last_prediction") || "null");
  if (!ctx || !ctx.predicted_yield_kg_ha) {
    contextCard.innerHTML =
      "<p>No prediction made yet. Go to the <strong>Predict</strong> page and make a prediction first, or ask general crop questions below.</p>";
    return;
  }
  contextCard.innerHTML = `<div class="ctxMini">
    <p><strong>Crop:</strong> ${ctx.Crop_Type || "—"}</p>
    <p><strong>State:</strong> ${ctx.State || "—"}</p>
    <p><strong>Yield:</strong> ${Math.round(ctx.predicted_yield_kg_ha)} kg/ha</p>
    <p><strong>Category:</strong> ${categoryChip(ctx.predicted_category)}</p>
    <p><strong>N:</strong> ${ctx.N_kgha ?? "—"} kg/ha</p>
    <p><strong>Rainfall:</strong> ${ctx.Rainfall_mm ?? "—"} mm</p>
    <p><strong>Soil pH:</strong> ${ctx.Soil_pH ?? "—"}</p>
    <p class="ctxNote">The AI assistant is aware of your last prediction and will use this context when answering your questions.</p>
  </div>`;
}

function showTyping() {
  const el = document.createElement("div");
  el.className = "chatBubble bot typingBubble";
  el.id = "typingIndicator";
  el.innerHTML = "<span class='dot'></span><span class='dot'></span><span class='dot'></span>";
  historyEl.appendChild(el);
  historyEl.scrollTop = historyEl.scrollHeight;
}
function hideTyping() {
  document.getElementById("typingIndicator")?.remove();
}

async function sendMessage(text) {
  const hist = loadHistory();
  const prior = [...hist];
  hist.push({ role: "user", content: text, time: new Date().toLocaleTimeString() });
  saveHistory(hist);
  render();
  showTyping();
  const predictionContext = JSON.parse(localStorage.getItem("last_prediction") || "{}");
  let json = { reply: "Network error." };
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        prediction_context: predictionContext,
        chat_history: prior,
      }),
    });
    json = await res.json();
  } catch (_) {
    /* keep default */
  }
  hideTyping();
  hist.push({ role: "assistant", content: json.reply || "No response.", time: new Date().toLocaleTimeString() });
  saveHistory(hist);
  render();
}

sendBtn.onclick = () => {
  const t = input.value.trim();
  if (!t) return;
  input.value = "";
  sendMessage(t);
};
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendBtn.click();
  }
});

document.getElementById("clearChat").onclick = () => {
  localStorage.removeItem("chat_history");
  saveHistory([
    { role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() },
  ]);
  render();
};
document.getElementById("newSession").onclick = () => {
  localStorage.removeItem("chat_history");
  localStorage.removeItem("last_prediction");
  localStorage.removeItem("prediction_made");
  saveHistory([
    { role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() },
  ]);
  render();
  renderContext();
};
document.getElementById("exportChat").onclick = () => {
  const txt = loadHistory().map((m) => `[${m.time}] ${m.role}: ${m.content}`).join("\n\n");
  const blob = new Blob([txt], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "cropai_chat.txt";
  a.click();
};

chips.forEach((c) => {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "chip";
  b.textContent = c;
  b.onclick = () => sendMessage(c);
  chipsEl.appendChild(b);
});

if (!loadHistory().length) {
  saveHistory([{ role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() }]);
}
render();
renderContext();
