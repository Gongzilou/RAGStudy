"use strict";

const DEFAULT_API_URL = "http://127.0.0.1:8000/chat";
const API_URL_STORAGE_KEY = "ragstudy.apiUrl";

const form = document.querySelector("#chatForm");
const input = document.querySelector("#questionInput");
const sendButton = document.querySelector("#sendButton");
const sendButtonText = document.querySelector("#sendButtonText");
const characterCount = document.querySelector("#characterCount");
const welcome = document.querySelector("#welcome");
const messageList = document.querySelector("#messageList");
const clearButton = document.querySelector("#clearButton");
const connectionState = document.querySelector("#connectionState");
const connectionLabel = document.querySelector("#connectionLabel");
const suggestionButtons = document.querySelectorAll("[data-question]");

let isSending = false;

function setConnectionState(state, label) {
  connectionState.classList.remove("is-connected", "is-loading", "is-error");
  if (state) {
    connectionState.classList.add(`is-${state}`);
  }
  connectionLabel.textContent = label;
}

function setBusy(busy) {
  isSending = busy;
  input.disabled = busy;
  sendButton.disabled = busy;
  sendButtonText.textContent = busy ? "思考中" : "发送";
  if (!busy) {
    input.focus();
  }
}

function scrollToLatest() {
  requestAnimationFrame(() => {
    const conversation = document.querySelector(".conversation");
    conversation.scrollTop = conversation.scrollHeight;
  });
}

function createAvatar(isUser) {
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");

  if (isUser) {
    avatar.innerHTML =
      '<svg viewBox="0 0 20 20" fill="none"><path d="M10 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm-5.2 6.1c.5-2.1 2.5-3.6 5.2-3.6s4.7 1.5 5.2 3.6" stroke="currentColor" stroke-linecap="round" stroke-width="1.5"/></svg>';
  } else {
    avatar.innerHTML =
      '<svg viewBox="0 0 20 20" fill="none"><path d="M10 2.5v2m0 11v2m-7-7h2m10 0h2m-12-5 1.4 1.4m7.2 7.2L15 15m0-10-1.4 1.4m-7.2 7.2L5 15" stroke="currentColor" stroke-linecap="round" stroke-width="1.3"/><path d="M10 6.5a3.5 3.5 0 0 0-2.4 6.1c.4.4.7.8.8 1.2h3.2c.1-.4.4-.8.8-1.2A3.5 3.5 0 0 0 10 6.5Z" stroke="currentColor" stroke-linejoin="round" stroke-width="1.3"/></svg>';
  }

  return avatar;
}

function addMessage(role, text, options = {}) {
  const isUser = role === "user";
  const message = document.createElement("article");
  message.className = `message ${role}`;
  if (options.pending) {
    message.setAttribute("aria-label", "助手正在生成回答");
  }

  const content = document.createElement("div");
  content.className = "message-content";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const name = document.createElement("strong");
  name.textContent = isUser ? "你" : "知答助手";
  const time = document.createElement("time");
  time.dateTime = new Date().toISOString();
  time.textContent = new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
  meta.append(name, time);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  if (options.pending) {
    bubble.classList.add("is-pending");
    bubble.setAttribute("aria-label", "正在查询知识库并生成回答");
    for (let index = 0; index < 3; index += 1) {
      const dot = document.createElement("span");
      dot.className = "typing-dot";
      bubble.append(dot);
    }
  } else {
    bubble.textContent = text;
    if (options.error) {
      bubble.classList.add("is-error");
    }
  }

  content.append(meta, bubble);
  if (isUser) {
    message.append(content, createAvatar(true));
  } else {
    message.append(createAvatar(false), content);
  }
  messageList.append(message);

  welcome.hidden = true;
  messageList.classList.add("is-visible");
  clearButton.disabled = false;
  scrollToLatest();
  return message;
}

function getApiUrl() {
  let configuredUrl = DEFAULT_API_URL;
  try {
    configuredUrl = localStorage.getItem(API_URL_STORAGE_KEY) || DEFAULT_API_URL;
  } catch (error) {
    console.warn("无法读取已保存的 API 地址，将使用默认地址。", error);
  }

  return configuredUrl.trim();
}

function describeRequestError(error) {
  if (error.name === "AbortError") {
    return "请求等待时间过长，已自动停止。请确认后端正在运行后重试。";
  }

  return [
    "无法连接到后端 API。",
    "请确认服务已启动，API 地址正确；如果前端与后端使用不同端口，请在后端启用 CORS 或通过同源代理访问。",
    `详细信息：${error.message || "网络请求失败"}`,
  ].join("\n");
}

async function askBackend(question, onChunk) {
  const apiUrl = getApiUrl();
  if (!apiUrl) {
    throw new Error("API 地址为空，请设置后端地址。");
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 180000);

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/plain",
      },
      body: JSON.stringify({ question }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const responseText = await response.text();
      let detail;
      try {
        const payload = responseText ? JSON.parse(responseText) : {};
        detail = typeof payload.detail === "string" ? payload.detail : "";
      } catch {
        detail = "";
      }
      throw new Error(
        detail || `后端请求失败（HTTP ${response.status}）。`,
      );
    }

    if (!response.body) {
      throw new Error("后端响应不包含可读取的数据流。");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let answer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        answer += chunk;
        onChunk(chunk);
      }
    }

    const finalChunk = decoder.decode();
    if (finalChunk) {
      answer += finalChunk;
      onChunk(finalChunk);
    }

    if (!answer.trim()) {
      throw new Error("后端返回了空回答。");
    }

    return answer;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function submitQuestion(question) {
  const trimmedQuestion = question.trim();
  if (!trimmedQuestion || isSending) {
    return;
  }

  addMessage("user", trimmedQuestion);
  input.value = "";
  updateCharacterCount();
  resizeInput();
  setBusy(true);
  setConnectionState("loading", "正在查询知识库");
  const pendingMessage = addMessage("assistant", "", { pending: true });
  const answerBubble = pendingMessage.querySelector(".message-bubble");
  let hasReceivedText = false;

  try {
    await askBackend(trimmedQuestion, (chunk) => {
      if (!hasReceivedText) {
        hasReceivedText = true;
        pendingMessage.removeAttribute("aria-label");
        answerBubble.classList.remove("is-pending");
        answerBubble.removeAttribute("aria-label");
        answerBubble.replaceChildren();
      }
      answerBubble.textContent += chunk;
      scrollToLatest();
    });
    setConnectionState("connected", "API 已连接");
  } catch (error) {
    const message =
      error instanceof TypeError
        ? describeRequestError(error)
        : error.message || "请求失败，请稍后重试。";
    if (!hasReceivedText) {
      pendingMessage.remove();
    }
    addMessage("assistant", message, { error: true });
    setConnectionState("error", "请求失败");
  } finally {
    setBusy(false);
  }
}

function updateCharacterCount() {
  characterCount.textContent = `${input.value.length} / 2000`;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(input.value);
});

input.addEventListener("input", () => {
  updateCharacterCount();
  resizeInput();
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  if (isSending) {
    return;
  }
  messageList.replaceChildren();
  messageList.classList.remove("is-visible");
  welcome.hidden = false;
  clearButton.disabled = true;
  setConnectionState("", "等待首次提问");
  input.focus();
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (isSending) {
      return;
    }
    submitQuestion(button.dataset.question);
  });
});

updateCharacterCount();
