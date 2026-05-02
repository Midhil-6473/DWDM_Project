const historyEl = document.getElementById("chatHistory");
const input = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendChat");
const contextCard = document.getElementById("contextCard");
const chipsEl = document.getElementById("chips");
const typingIndicator = document.getElementById("typingIndicator");

const chips = [
  "Why is my yield Low?",
  "How to increase my yield?",
  "Best crop for my region?",
  "What does NDVI mean?",
  "Optimal fertilizer for Rice?",
  "What is water stress index?",
  "Compare crops for Rabi season",
];

const WELCOME = "🌾 Hello! I am **CropAI** — your intelligent farming assistant.\n\nI can help you:\n• Understand your yield prediction\n• Suggest better crops for your soil\n• Advise on NPK fertilizer levels\n• Explain climate impacts on yield\n\nMake a prediction first, then ask me anything!";

let predictionCtx = {};
let isSending = false;

function loadHistory() { return JSON.parse(localStorage.getItem("chat_history") || "[]"); }
function saveHistory(h) { localStorage.setItem("chat_history", JSON.stringify(h)); }

// Simple markdown-like formatting
function formatMessage(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^• /gm, '&bull; ')
    .replace(/^(\d+)\. /gm, '<strong>$1.</strong> ')
    .replace(/\n/g, '<br/>');
}

function render() {
  const hist = loadHistory();
  historyEl.innerHTML = hist.map(m => `
    <div class="chatBubble ${m.role === "user" ? "user" : "bot"}">
      <div class="msgContent">${formatMessage(m.content)}</div>
      <small>${m.time}</small>
    </div>
  `).join("");
  historyEl.scrollTop = historyEl.scrollHeight;
}

function renderContext(ctx) {
  if (!ctx || !ctx.Crop_Type) {
    contextCard.innerHTML = "<p>No prediction data found. Make a prediction on the dashboard first.</p>";
    return;
  }
  const r = v => v != null ? Math.round(Number(v)).toLocaleString() : '—';
  contextCard.innerHTML = `
    <div style="background:rgba(46,125,50,0.1);padding:10px 12px;border-radius:10px;margin-bottom:12px;border:1px solid rgba(46,125,50,0.2);font-size:0.9rem;">
      <strong style="color:var(--green);">${ctx.Crop_Type}</strong> in ${ctx.State}<br/>
      <span style="font-size:0.8rem;color:var(--text-muted);">Season: ${ctx.Season}</span>
    </div>
    <table style="width:100%;font-size:0.85rem;border-collapse:collapse;">
      <tr><td style="padding:4px 0;color:var(--text-muted);">Predicted</td><td style="padding:4px 0;text-align:right;font-weight:700;">${r(ctx.predicted_yield_kg_ha)} kg/ha</td></tr>
      <tr><td style="padding:4px 0;color:var(--text-muted);">Category</td><td style="padding:4px 0;text-align:right;font-weight:700;">${ctx.predicted_category}</td></tr>
      <tr><td style="padding:4px 0;color:var(--text-muted);">Best Crop</td><td style="padding:4px 0;text-align:right;font-weight:700;">${ctx.recommended_crop || '—'}</td></tr>
    </table>
    <div style="margin-top:10px;padding:8px 10px;border-radius:8px;background:rgba(0,0,0,0.03);border:1px solid var(--border);font-size:0.78rem;color:var(--text-muted);line-height:1.6;">
      <strong>N:</strong> ${r(ctx.N_kgha)} · <strong>P:</strong> ${r(ctx.P_kgha)} · <strong>K:</strong> ${r(ctx.K_kgha)} kg/ha<br/>
      <strong>Rain:</strong> ${r(ctx.Rainfall_mm)} mm · <strong>pH:</strong> ${Number(ctx.Soil_pH || 0).toFixed(1)}
    </div>
  `;
}

async function fetchPredictionContext() {
  try {
    const resp = await fetch('/api/prediction-context');
    if (!resp.ok) throw new Error('Failed');
    const data = await resp.json();
    predictionCtx = data.context || {};
    renderContext(predictionCtx);
  } catch (e) {
    const local = JSON.parse(localStorage.getItem("last_prediction") || "null");
    predictionCtx = local || {};
    renderContext(predictionCtx);
  }
}

function showTyping() {
  typingIndicator.style.display = 'flex';
  historyEl.scrollTop = historyEl.scrollHeight;
}

function hideTyping() {
  typingIndicator.style.display = 'none';
}

function setInputState(disabled) {
  isSending = disabled;
  input.disabled = disabled;
  sendBtn.disabled = disabled;
  sendBtn.textContent = disabled ? '...' : 'Send';
}

// Typewriter effect for bot messages
async function typewriterRender(fullText) {
  const hist = loadHistory();
  // Add placeholder
  hist.push({ role: "assistant", content: "", time: new Date().toLocaleTimeString() });
  saveHistory(hist);
  render();

  const bubbles = historyEl.querySelectorAll('.chatBubble.bot');
  const lastBubble = bubbles[bubbles.length - 1];
  const contentEl = lastBubble.querySelector('.msgContent');

  // Split into words for natural typing
  const words = fullText.split(' ');
  let current = '';
  
  for (let i = 0; i < words.length; i++) {
    current += (i > 0 ? ' ' : '') + words[i];
    contentEl.innerHTML = formatMessage(current);
    historyEl.scrollTop = historyEl.scrollHeight;
    
    // Variable speed: faster for short words, slight pause after punctuation
    const word = words[i];
    let delay = 25 + Math.random() * 20;
    if (word.endsWith('.') || word.endsWith('!') || word.endsWith('?') || word.endsWith(':')) delay = 80;
    if (word.endsWith(',')) delay = 40;
    await new Promise(r => setTimeout(r, delay));
  }

  // Update history with full text
  const finalHist = loadHistory();
  finalHist[finalHist.length - 1].content = fullText;
  saveHistory(finalHist);
}

async function sendMessage(text) {
  if (isSending) return;
  
  const hist = loadHistory();
  const prior = [...hist];
  hist.push({ role: "user", content: text, time: new Date().toLocaleTimeString() });
  saveHistory(hist);
  render();
  
  setInputState(true);
  showTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, prediction_context: predictionCtx, chat_history: prior.slice(-10) })
    });
    const data = await res.json();
    
    hideTyping();
    await typewriterRender(data.reply);
  } catch (err) {
    hideTyping();
    const hist2 = loadHistory();
    hist2.push({ role: "assistant", content: "⚠️ Sorry, I couldn't process your request. Please try again.", time: new Date().toLocaleTimeString() });
    saveHistory(hist2);
    render();
  } finally {
    setInputState(false);
    input.focus();
  }
}

sendBtn.onclick = () => {
  const t = input.value.trim();
  if (!t || isSending) return;
  input.value = "";
  sendMessage(t);
};
input.onkeypress = (e) => { if (e.key === "Enter" && !isSending) sendBtn.click(); };

document.getElementById("clearChat").onclick = () => {
  localStorage.removeItem("chat_history");
  saveHistory([{ role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() }]);
  render();
};

document.getElementById("exportChat").onclick = () => {
  const txt = loadHistory().map(m => `[${m.time}] ${m.role}: ${m.content}`).join("\n\n");
  const blob = new Blob([txt], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "cropai_chat.txt";
  a.click();
};

document.getElementById("newSession").onclick = () => {
  localStorage.removeItem("chat_history");
  saveHistory([{ role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() }]);
  render();
  fetchPredictionContext();
};

// Check AI status
async function checkAIStatus() {
  try {
    const resp = await fetch('/api/chat/status');
    const data = await resp.json();
    const dot = document.getElementById('aiStatusDot');
    const text = document.getElementById('aiStatusText');
    const info = document.getElementById('aiModelInfo');
    if (data.gemini_enabled) {
      dot.style.background = '#22c55e';
      text.textContent = 'Gemini AI Online';
      info.textContent = 'Powered by Google Gemini';
    } else {
      dot.style.background = '#FB8C00';
      text.textContent = 'Basic AI Mode';
      info.textContent = 'Rule-based responses (add Gemini API key for smarter answers)';
    }
  } catch (e) {
    // ignore
  }
}

chips.forEach(c => {
  const b = document.createElement("button");
  b.className = "chip";
  b.textContent = c;
  b.onclick = () => { if (!isSending) sendMessage(c); };
  chipsEl.appendChild(b);
});

if (!loadHistory().length) saveHistory([{ role: "assistant", content: WELCOME, time: new Date().toLocaleTimeString() }]);
render();
fetchPredictionContext();
checkAIStatus();
