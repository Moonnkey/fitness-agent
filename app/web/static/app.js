const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const summaryButton = document.querySelector("#summaryButton");

function appendMessage(text, role = "assistant") {
  const element = document.createElement("div");
  element.className = `message ${role}`;
  element.textContent = text;
  messages.appendChild(element);
  messages.scrollTop = messages.scrollHeight;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";
  sendButton.disabled = true;

  try {
    const data = await postJson("/api/chat", {message: text});
    appendMessage(data.reply || "操作已完成。", "assistant");
  } catch (error) {
    appendMessage(`请求失败：${error.message}`, "error");
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
});

summaryButton.addEventListener("click", async () => {
  summaryButton.disabled = true;
  try {
    const summary = await getJson("/api/summary/today");
    appendMessage(
      `今天目前总摄入 ${summary.total_calories ?? 0} kcal，蛋白质 ${
        summary.total_protein_g ?? 0
      } g，剩余目标热量 ${summary.remaining_calories ?? "未知"} kcal。`,
      "assistant",
    );
  } catch (error) {
    appendMessage(`查询失败：${error.message}`, "error");
  } finally {
    summaryButton.disabled = false;
  }
});
