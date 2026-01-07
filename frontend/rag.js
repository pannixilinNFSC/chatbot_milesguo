const STORAGE_KEY = "chatbot-milesguo:settings:v1";

function renderSourcesDetails(container, sources, { includeIndex = true } = {}) {
  if (!sources || !Array.isArray(sources) || sources.length === 0) return;

  const details = document.createElement("details");
  details.open = !!showSources.checked;

  const summary = document.createElement("summary");
  summary.textContent = `Sources (${sources.length})`;
  details.appendChild(summary);

  const list = document.createElement("div");
  list.className = "sources";

  for (const s of sources) {
    const item = document.createElement("div");
    item.className = "sourceItem";

    const title = document.createElement("p");
    title.className = "sourceTitle";
    title.textContent = s.doc_title || "(untitled)";

    const metaP = document.createElement("p");
    metaP.className = "sourceMeta";
    const index = s.index ?? "";
    const chunkId = s.chunk_id ?? "";
    const docId = s.doc_id ?? "";
    const score = s.score != null ? Number(s.score).toFixed(4) : "";
    const indexPrefix = includeIndex && index !== "" ? `#${index}   ` : "";
    metaP.textContent = `${indexPrefix}doc_id: ${docId}   chunk_id: ${chunkId}   score: ${score}`;

    const textP = document.createElement("p");
    textP.className = "sourceText";
    textP.textContent = s.text ? `Chunk: ${s.text}` : "";

    const summaryText = s.doc_summary || s.summary || "";
    if (summaryText) {
      const summaryP = document.createElement("p");
      summaryP.className = "sourceText";
      summaryP.textContent = `Summary: ${summaryText}`;
      item.appendChild(summaryP);
    }

    const context = s.context || "";
    if (context) {
      const contextP = document.createElement("p");
      contextP.className = "sourceText";
      contextP.textContent = `Context: ${context}`;
      item.appendChild(contextP);
    }

    item.appendChild(title);
    item.appendChild(metaP);
    item.appendChild(textP);
    list.appendChild(item);
  }

  details.appendChild(list);
  container.appendChild(details);
}

function renderSourcesProgress(container, sources) {
  if (!sources || !Array.isArray(sources) || sources.length === 0) return;
  const progressDiv = document.createElement("div");
  progressDiv.className = "progressIndicator fadeIn";
  progressDiv.innerHTML = `
          <div class="progressDot"></div>
          <span class="progressText">Found ${sources.length} source${sources.length !== 1 ? "s" : ""}</span>
        `;
  container.appendChild(progressDiv);
}

function addMessage({ role, text, sources = null, prompt = null, querys = null, thinking = false, updateBubble = null, useTypewriter = true }) {
  // If updateBubble is provided, update existing message instead of creating new one
  if (updateBubble) {
    const pre = updateBubble.querySelector(".msg");
    if (pre) {
      if (thinking) {
        pre.innerHTML = '<span class="thinking">Thinking</span>';
      } else {
        // Remove typing class if present
        pre.classList.remove("typing");
        if (useTypewriter && text) {
          typewriterEffect(pre, text);
        } else {
          pre.textContent = text || "";
        }
      }
    }

    // Remove existing progress indicator if any
    const existingProgress = updateBubble.querySelectorAll(".progressIndicator");
    existingProgress.forEach(p => p.remove());
    
    // Remove existing sources/details if any
    const existingDetails = updateBubble.querySelectorAll("details");
    existingDetails.forEach(d => d.remove());

    // Add new sources if provided
    if (role === "assistant") {
      renderSourcesProgress(updateBubble, sources);
      renderSourcesDetails(updateBubble, sources);
    }

    messages.scrollTop = messages.scrollHeight;
    return updateBubble;
  }

  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;

  const meta = document.createElement("div");
  meta.className = "meta";
  
  const metaLeft = document.createElement("span");
  metaLeft.textContent = role === "user" ? "You" : "Assistant";
  
  const metaRight = document.createElement("span");
  metaRight.textContent = nowTime();
  
  // Add message action buttons
  const messageActions = document.createElement("div");
  messageActions.className = "messageActions";
  
  if (role === "user" && !thinking) {
    const editBtn = document.createElement("button");
    editBtn.className = "messageActionBtn";
    editBtn.innerHTML = "✏️ Edit";
    editBtn.title = "Edit message";
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      // Put text back into input
      userInput.value = text || "";
      userInput.focus();
      // Remove this message and all following messages
      const allBubbles = Array.from(messages.children);
      const currentIndex = allBubbles.indexOf(bubble);
      for (let i = currentIndex + 1; i < allBubbles.length; i++) {
        allBubbles[i].remove();
      }
      // Update query context
      const removedCount = allBubbles.length - currentIndex - 1;
      queryContext = queryContext.slice(0, -removedCount * 2);
    });
    messageActions.appendChild(editBtn);
  }
  
  if (role === "assistant" && !thinking) {
    const copyBtn = document.createElement("button");
    copyBtn.className = "messageActionBtn";
    copyBtn.innerHTML = "📋 Copy";
    copyBtn.title = "Copy message";
    copyBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const success = await copyToClipboard(text || "");
      if (success) {
        copyBtn.innerHTML = "✓ Copied";
        copyBtn.classList.add("success");
        setTimeout(() => {
          copyBtn.innerHTML = "📋 Copy";
          copyBtn.classList.remove("success");
        }, 2000);
      }
    });
    
    const regenerateBtn = document.createElement("button");
    regenerateBtn.className = "messageActionBtn";
    regenerateBtn.innerHTML = "🔄 Regenerate";
    regenerateBtn.title = "Regenerate response";
    regenerateBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      // Find the previous user message
      const allBubbles = Array.from(messages.children);
      const currentIndex = allBubbles.indexOf(bubble);
      for (let i = currentIndex - 1; i >= 0; i--) {
        if (allBubbles[i].classList.contains("user")) {
          const userText = allBubbles[i].querySelector(".msg")?.textContent || "";
          if (userText) {
            // Remove this assistant message and all messages after it
            for (let j = currentIndex; j < allBubbles.length; j++) {
              allBubbles[j].remove();
            }
            // Update query context
            const removedCount = allBubbles.length - currentIndex;
            queryContext = queryContext.slice(0, -removedCount * 2);
            // Set user input and send
            userInput.value = userText;
            sendMessage();
            break;
          }
        }
      }
    });
    
    messageActions.appendChild(copyBtn);
    messageActions.appendChild(regenerateBtn);
  }
  
  meta.appendChild(metaLeft);
  meta.appendChild(messageActions);
  meta.appendChild(metaRight);

  const pre = document.createElement("pre");
  pre.className = "msg";
  if (thinking) {
    pre.innerHTML = '<span class="thinking">Thinking</span>';
  } else {
    if (useTypewriter && text && role === "assistant") {
      // Start typewriter effect
      typewriterEffect(pre, text);
    } else {
      pre.textContent = text || "";
    }
  }

  bubble.appendChild(meta);
  bubble.appendChild(pre);

  if (role === "assistant") {
    renderSourcesProgress(bubble, sources);
    renderSourcesDetails(bubble, sources, { includeIndex: false });
  }

  if (role === "assistant") {
    if (querys && querys.length) {
      const d = document.createElement("details");
      d.innerHTML = `<summary>Queries (${querys.length})</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em;max-height:200px;overflow:auto">${querys.map((q, i) => `${i ? 'Expanded ' + i : 'Original'}: ${q}`).join('\n')}</pre>`;
      bubble.appendChild(d);
    }
    if (prompt) {
      const d = document.createElement("details");
      d.innerHTML = `<summary>Prompt</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.85em;max-height:400px;overflow:auto;background:#f5f5f5">${prompt}</pre>`;
      bubble.appendChild(d);
    }
  }

  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

function getSettingsFromUI() {
  // Clamp values to valid ranges
  const chunkKValue = Number(chunkK.value || 10);
  const queryExpandKValue = Number(queryExpandK.value || 1);
  
  return {
    cloudBase: cloudBase.value.trim(),
    authToken: getAuthToken(),
    titleK: Number(titleK.value || 3),
    chunkK: Math.max(1, Math.min(12, chunkKValue)),
    queryExpandK: Math.max(1, Math.min(3, queryExpandKValue)),
    chunkIndex: chunkIndex.value.trim() || null,
  };
}

function applySettingsToUI(s) {
  cloudBase.value = s.cloudBase ?? "";
  titleK.value = String(Number.isFinite(s.titleK) ? s.titleK : 3);
  chunkK.value = String(Number.isFinite(s.chunkK) ? s.chunkK : 10);
  queryExpandK.value = String(Number.isFinite(s.queryExpandK) ? s.queryExpandK : 1);
  chunkIndex.value = s.chunkIndex ?? "";
}

function loadSettings() {
  const defaults = {
    cloudBase: "https://us-central1-xixibaigao.cloudfunctions.net/chatbot-milesguo/chatbot_stream",
    titleK: 3,
    chunkK: 10,
    queryExpandK: 1,
    chunkIndex: "",
  };

  let settings = defaults;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      settings = { ...defaults, ...JSON.parse(raw) };
    }
  } catch {
    // Keep defaults
  }

  // Override with URL parameters if present
  const params = new URLSearchParams(window.location.search);
  const urlChunkIndex = params.get("chunk_index");
  if (urlChunkIndex !== null) {
    settings.chunkIndex = urlChunkIndex.trim();
  }

  return settings;
}

function saveSettings(s) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}


let inFlight = null;
let currentThinkingBubble = null;
let rateLimitTimer = null;
// Store conversation history for query_context
let queryContext = [];

function clearRateLimitTimer() {
  if (rateLimitTimer) {
    clearInterval(rateLimitTimer);
    rateLimitTimer = null;
  }
}

function startRateLimitCountdown(seconds) {
  clearRateLimitTimer();
  let remaining = Math.max(1, Math.floor(seconds || 1));
  sendBtn.disabled = true;

  setStatus(`Rate limited (${remaining}s)`, true);
  rateLimitTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearRateLimitTimer();
      setStatus("Idle");
      sendBtn.disabled = false;
      return;
    }
    setStatus(`Rate limited (${remaining}s)`, true);
  }, 1000);
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;
  errorLine.textContent = "";

  // Cancel previous request if in flight
  if (inFlight) {
    inFlight.abort();
    inFlight = null;
    // Mark previous thinking bubble as cancelled
    if (currentThinkingBubble) {
      const msgElement = currentThinkingBubble.querySelector(".msg");
      if (msgElement) {
        msgElement.textContent = "(Cancelled)";
        msgElement.classList.remove("typing");
      }
      const statusIndicator = currentThinkingBubble.querySelector(".progressIndicator");
      if (statusIndicator) {
        statusIndicator.innerHTML = `
          <div class="progressDot"></div>
          <span class="progressText">Cancelled</span>
        `;
      }
      currentThinkingBubble = null;
    }
  }

  // Ensure token is fetched before sending request
  if (!cachedAuthToken) {
    const fetchedToken = await fetchAuthTokenFromBackend();
    if (!fetchedToken && !getAuthToken()) {
      // If no token from URL param and fetch returned null, warn user
      console.warn("No authentication token available. Backend may require authentication.");
    }
  }

  const s = getSettingsFromUI();
  const endpoint = buildEndpointUrl(s.cloudBase);
  if (!endpoint) {
    errorLine.textContent = "Please fill Cloud Functions URL.";
    return;
  }
  
  // Validate URL format
  try {
    new URL(endpoint);
  } catch (e) {
    errorLine.textContent = "Invalid URL format. Please enter a valid Cloud Functions URL.";
    setStatus("Invalid URL", true);
    return;
  }

  addMessage({ role: "user", text });
  userInput.value = "";

  // Determine if we should use streaming endpoint
  // Only use streaming if the URL explicitly contains /chatbot_stream
  // User must explicitly specify streaming endpoint in the URL
  let useStreaming = false;
  
  // Check if URL explicitly contains streaming endpoint
  if (endpoint.includes("/chatbot_stream")) {
    useStreaming = true;
  }

  // Use the full URL directly (user can specify complete endpoint like /chatbot or /chatbot_stream)
  const url = new URL(endpoint);
  url.searchParams.set("txt_query", text);
  url.searchParams.set("title_k", String(s.titleK));
  url.searchParams.set("chunk_k", String(s.chunkK));
  url.searchParams.set("query_expand_k", String(s.queryExpandK));
  // Add chunk_index if provided (title_index is computed from chunk_index on backend)
  if (s.chunkIndex) {
    url.searchParams.set("chunk_index", s.chunkIndex);
  }
  // Add query_context if available
  if (queryContext && queryContext.length > 0) {
    for (const contextItem of queryContext) {
      url.searchParams.append("query_context", contextItem);
    }
  }

  const controller = new AbortController();
  inFlight = controller;

  clearRateLimitTimer();
  sendBtn.disabled = true;
  cancelBtn.disabled = false;
  setStatus("Requesting…");

  // Add thinking indicator for assistant with enhanced status
  const thinkingBubble = addMessage({ role: "assistant", thinking: true });
  currentThinkingBubble = thinkingBubble;
  
  // Add status indicator to thinking bubble
  const statusIndicator = document.createElement("div");
  statusIndicator.className = "progressIndicator";
  statusIndicator.innerHTML = `
    <div class="progressDot"></div>
    <span class="progressText">${useStreaming ? "Connecting to stream..." : "Searching knowledge base..."}</span>
  `;
  thinkingBubble.appendChild(statusIndicator);

  try {
    // Get fresh token in case it was just fetched
    const authToken = getAuthToken();
    const headers = {
      Accept: useStreaming ? "text/event-stream" : "application/json",
    };
    
    // Always include Authorization header if token exists
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
      console.log("Sending request with Authorization header");
    } else {
      console.warn("No auth token available - request may fail if backend requires authentication");
    }
    
    if (useStreaming) {
      // Use streaming response with EventSource-like handling
      await handleStreamingResponse(url.toString(), headers, controller, thinkingBubble, text);
    } else {
      // Use regular non-streaming response
      await handleNonStreamingResponse(url.toString(), headers, controller, thinkingBubble, text);
    }
  } catch (e) {
    // Only show error if not cancelled (cancelled requests are already handled above)
    if (e?.name !== "AbortError" || thinkingBubble === currentThinkingBubble) {
      const msg = e?.name === "AbortError" ? "Request cancelled." : String(e?.message || e);
      addMessage({ role: "assistant", text: `Error: ${msg}`, updateBubble: thinkingBubble, useTypewriter: false });
      setStatus("Error", true);
      errorLine.textContent = msg;
    }
  } finally {
    inFlight = null;
    currentThinkingBubble = null;
    // If we are counting down for rate limiting, keep send disabled.
    if (!rateLimitTimer) sendBtn.disabled = false;
    cancelBtn.disabled = true;
  }
}

async function handleStreamingResponse(url, headers, controller, thinkingBubble, userText) {
  const res = await fetch(url, {
    method: "GET",
    signal: controller.signal,
    headers: headers,
  });

  if (!res.ok) {
    if (res.status === 401) {
      const tokenInfo = headers.Authorization ? "Token is present but invalid" : "No token provided";
      throw new Error(`Unauthorized (401). ${tokenInfo}. Check API_AUTH_TOKEN environment variable on backend or include token in URL parameter: ?token=xxx`);
    }
    if (res.status === 429) {
      const retryAfterHeader = res.headers.get("Retry-After");
      const retryAfter = Number(retryAfterHeader || "");
      if (Number.isFinite(retryAfter) && retryAfter > 0) {
        startRateLimitCountdown(retryAfter);
        throw new Error(`Rate limit exceeded (429). Retry after ${retryAfter}s.`);
      }
      throw new Error("Rate limit exceeded (429). Please retry later.");
    }
    const detail = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";
  let sources = null;
  let prompt = null;
  let querys = null;

  // Get the message element for streaming updates
  const msgElement = thinkingBubble.querySelector(".msg");
  if (!msgElement) {
    throw new Error("Message element not found");
  }

  // Remove thinking indicator and prepare for streaming
  msgElement.innerHTML = "";
  msgElement.classList.remove("typing");
  msgElement.classList.add("typing");
  
  // Update status to show streaming
  const statusIndicator = thinkingBubble.querySelector(".progressIndicator");
  if (statusIndicator) {
    statusIndicator.innerHTML = `
      <div class="progressDot"></div>
      <span class="progressText">Generating response...</span>
    `;
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue; // Skip empty lines
        if (line.startsWith("data: ")) {
          try {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue; // Skip empty data lines
            const data = JSON.parse(jsonStr);
            const { type, data: chunkData } = data;

            if (type === "content") {
              // Stream content chunks only
              fullContent += chunkData;
              msgElement.textContent = fullContent;
              messages.scrollTop = messages.scrollHeight;
            } else if (type === "done") {
              // Final update with all data
              fullContent = chunkData.content || fullContent;
              sources = chunkData.search_results || sources || [];
              prompt = chunkData.prompt || prompt;
              querys = chunkData.querys || querys;
              break;
            } else if (type === "error") {
              throw new Error(chunkData.error || "Unknown error");
            }
          } catch (e) {
            console.error("Error parsing SSE data:", e, line);
          }
        }
      }
    }

    // Remove typing cursor
    msgElement.classList.remove("typing");

    // Update message with final content and sources
    addMessage({
      role: "assistant",
      text: fullContent,
      sources,
      prompt,
      querys,
      updateBubble: thinkingBubble,
      useTypewriter: false, // Already displayed via streaming
    });

    // Keep the last 3 Q&A pairs (6 messages) for context
    queryContext.push(`用户: ${userText}`, `助手: ${fullContent}`);
    if (queryContext.length > 6) {
      queryContext = queryContext.slice(-6);
    }
    setStatus("Done");
  } catch (e) {
    msgElement.classList.remove("typing");
    throw e;
  }
}

async function handleNonStreamingResponse(url, headers, controller, thinkingBubble, userText) {
  const res = await fetch(url, {
    method: "GET",
    signal: controller.signal,
    headers: headers,
  });

  const retryAfterHeader = res.headers.get("Retry-After");
  const raw = await res.text();
  let data = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    data = null;
  }

  if (!res.ok) {
    if (res.status === 401) {
      const tokenInfo = headers.Authorization ? "Token is present but invalid" : "No token provided";
      throw new Error(`Unauthorized (401). ${tokenInfo}. Check API_AUTH_TOKEN environment variable on backend or include token in URL parameter: ?token=xxx`);
    }
    if (res.status === 429) {
      const retryAfter = Number(retryAfterHeader || "");
      if (Number.isFinite(retryAfter) && retryAfter > 0) {
        startRateLimitCountdown(retryAfter);
        throw new Error(`Rate limit exceeded (429). Retry after ${retryAfter}s.`);
      }
      throw new Error("Rate limit exceeded (429). Please retry later.");
    }
    const detail = data?.detail || raw || `HTTP ${res.status}`;
    throw new Error(detail);
  }

  const content = data?.content ?? "";
  const sources = Array.isArray(data?.search_results) ? data.search_results : [];
  const prompt = data?.prompt ?? null;
  const querys = Array.isArray(data?.querys) ? data.querys : null;
  
  addMessage({ 
    role: "assistant", 
    text: content, 
    sources, 
    prompt, 
    querys, 
    updateBubble: thinkingBubble,
    useTypewriter: true 
  });
  
  // Keep the last 3 Q&A pairs (6 messages) for context
  queryContext.push(`用户: ${userText}`, `助手: ${content}`);
  // Keep only the last 6 messages (3 rounds of Q&A)
  if (queryContext.length > 6) {
    queryContext = queryContext.slice(-6);
  }
  setStatus("Done");
}

// Wire up UI
const cloudBase = document.getElementById("cloudBase");
const titleK = document.getElementById("titleK");
const chunkK = document.getElementById("chunkK");
const queryExpandK = document.getElementById("queryExpandK");
const chunkIndex = document.getElementById("chunkIndex");
const statusPill = document.getElementById("statusPill");
const saveBtn = document.getElementById("saveBtn");
const resetBtn = document.getElementById("resetBtn");
const clearBtn = document.getElementById("clearBtn");
const showSources = document.getElementById("showSources");
const messages = document.getElementById("messages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const cancelBtn = document.getElementById("cancelBtn");
const errorLine = document.getElementById("errorLine");

// Add validation for chunkK and queryExpandK to ensure values stay within bounds
chunkK.addEventListener("input", () => {
  const value = Number(chunkK.value);
  if (value < 1) chunkK.value = "1";
  if (value > 12) chunkK.value = "12";
});
chunkK.addEventListener("change", () => {
  const value = Number(chunkK.value);
  if (value < 1) chunkK.value = "1";
  if (value > 12) chunkK.value = "12";
});

queryExpandK.addEventListener("input", () => {
  const value = Number(queryExpandK.value);
  if (value < 1) queryExpandK.value = "1";
  if (value > 3) queryExpandK.value = "3";
});
queryExpandK.addEventListener("change", () => {
  const value = Number(queryExpandK.value);
  if (value < 1) queryExpandK.value = "1";
  if (value > 3) queryExpandK.value = "3";
});

// Auto-fetch token when base URL changes
cloudBase.addEventListener("change", () => {
  cachedAuthToken = null;
  tokenFetchPromise = null;
  fetchAuthTokenFromBackend();
});

saveBtn.addEventListener("click", () => {
  const s = getSettingsFromUI();
  saveSettings(s);
  setStatus("Saved");
  setTimeout(() => setStatus("Idle"), 800);
});

resetBtn.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  applySettingsToUI(loadSettings());
  setStatus("Reset");
  setTimeout(() => setStatus("Idle"), 800);
});

clearBtn.addEventListener("click", () => {
  messages.innerHTML = "";
  errorLine.textContent = "";
  queryContext = [];
  setStatus("Cleared");
  setTimeout(() => setStatus("Idle"), 800);
});

sendBtn.addEventListener("click", sendMessage);
cancelBtn.addEventListener("click", () => {
  if (inFlight) {
    inFlight.abort();
    inFlight = null;
    // Mark thinking bubble as cancelled
    if (currentThinkingBubble) {
      const msgElement = currentThinkingBubble.querySelector(".msg");
      if (msgElement) {
        msgElement.textContent = "(Cancelled)";
        msgElement.classList.remove("typing");
      }
      const statusIndicator = currentThinkingBubble.querySelector(".progressIndicator");
      if (statusIndicator) {
        statusIndicator.innerHTML = `
          <div class="progressDot"></div>
          <span class="progressText">Cancelled</span>
        `;
      }
      currentThinkingBubble = null;
    }
  }
});

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Init
applySettingsToUI(loadSettings());
setStatus("Idle");
// Auto-fetch auth token from backend on page load
fetchAuthTokenFromBackend();
addMessage({
  role: "assistant",
  text: "请提问",
});

