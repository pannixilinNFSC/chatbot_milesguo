const STORAGE_KEY = "chatbot-milesguo:settings:v1";

function trimSlash(s) {
  return String(s || "").replace(/\/+$/, "");
}

function buildEndpointUrl({ cloudBase, functionName, endpointPath }) {
  const baseRaw = String(cloudBase || "").trim();
  const base = trimSlash(baseRaw);
  const fn = String(functionName || "").trim().replace(/^\/+|\/+$/g, "");
  const ep = String(endpointPath || "").trim().replace(/^\/+|\/+$/g, "");

  if (!base || !fn || !ep) return "";

  // Avoid double-appending if the user pastes a Cloud Functions URL that already includes
  // the function name (and/or endpoint path).
  try {
    const u = new URL(baseRaw);
    const segs = u.pathname.split("/").filter(Boolean);
    const last = segs[segs.length - 1];
    const secondLast = segs[segs.length - 2];

    // Case A: base already ends with /<function>/<endpoint>
    if (secondLast === fn && last === ep) {
      return trimSlash(u.toString());
    }
    // Case B: base already ends with /<function>
    if (last === fn) {
      return `${trimSlash(u.toString())}/${encodeURIComponent(ep)}`;
    }
  } catch {
    // Not a valid URL; fall back to simple concatenation.
  }

  return `${base}/${encodeURIComponent(fn)}/${encodeURIComponent(ep)}`;
}

function setStatus(text, isError = false) {
  statusPill.textContent = text;
  statusPill.classList.toggle("danger", isError);
}

function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addMessage({ role, text, sources = null, thinking = false, updateBubble = null }) {
  // If updateBubble is provided, update existing message instead of creating new one
  if (updateBubble) {
    const pre = updateBubble.querySelector(".msg");
    if (pre) {
      if (thinking) {
        pre.innerHTML = '<span class="thinking">Thinking</span>';
      } else {
        pre.textContent = text || "";
      }
    }

    // Remove existing sources if any
    const existingDetails = updateBubble.querySelector("details");
    if (existingDetails) {
      existingDetails.remove();
    }

    // Add new sources if provided
    if (role === "assistant" && sources && Array.isArray(sources) && sources.length > 0) {
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
        metaP.textContent = `#${index}   doc_id: ${docId}   chunk_id: ${chunkId}   score: ${score}`;

        const textP = document.createElement("p");
        textP.className = "sourceText";
        textP.textContent = s.text || "";

        item.appendChild(title);
        item.appendChild(metaP);
        item.appendChild(textP);
        list.appendChild(item);
      }

      details.appendChild(list);
      updateBubble.appendChild(details);
    }

    messages.scrollTop = messages.scrollHeight;
    return updateBubble;
  }

  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = `<span>${role === "user" ? "You" : "Assistant"}</span><span>${nowTime()}</span>`;

  const pre = document.createElement("pre");
  pre.className = "msg";
  if (thinking) {
    pre.innerHTML = '<span class="thinking">Thinking</span>';
  } else {
    pre.textContent = text || "";
  }

  bubble.appendChild(meta);
  bubble.appendChild(pre);

  if (role === "assistant" && sources && Array.isArray(sources) && sources.length > 0) {
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
      const chunkId = s.chunk_id ?? "";
      const docId = s.doc_id ?? "";
      const score = s._score ?? "";
      metaP.textContent = `doc_id: ${docId}   chunk_id: ${chunkId}   score: ${score}`;

      const textP = document.createElement("p");
      textP.className = "sourceText";
      textP.textContent = s.text || "";

      item.appendChild(title);
      item.appendChild(metaP);
      item.appendChild(textP);
      list.appendChild(item);
    }

    details.appendChild(list);
    bubble.appendChild(details);
  }

  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

let cachedAuthToken = null;
let tokenFetchPromise = null;

async function fetchAuthTokenFromBackend() {
  if (tokenFetchPromise) return tokenFetchPromise;
  
  tokenFetchPromise = (async () => {
    try {
      // Use DOM values directly to avoid circular dependency.
      // Build the token URL via the same path-normalization logic as the main endpoint URL,
      // so it still works if the user pastes a Cloud Functions URL that already contains
      // the function name (or even an endpoint path).
      const baseUrl = (cloudBase?.value || "").trim() || "https://us-central1-xixibaigao.cloudfunctions.net/";
      const funcName = (functionName?.value || "").trim() || "chatbot-milesguo";
      const tokenUrl = buildEndpointUrl({ cloudBase: baseUrl, functionName: funcName, endpointPath: "token" });
      if (!tokenUrl) {
        console.warn("Token URL is empty (check Cloud base URL and function name).");
        return null;
      }
      console.log("Fetching auth token from:", tokenUrl);
      
      const res = await fetch(tokenUrl, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      
      if (res.ok) {
        const data = await res.json();
        cachedAuthToken = data.token || null;
        if (cachedAuthToken) {
          // Trim token to avoid whitespace issues
          cachedAuthToken = cachedAuthToken.trim();
          console.log("Auth token fetched successfully");
        } else {
          console.warn("Auth token is null - authentication may not be enabled on backend");
        }
        return cachedAuthToken;
      } else {
        console.warn(`Failed to fetch auth token: ${res.status} ${res.statusText}`);
      }
    } catch (e) {
      console.warn("Failed to fetch auth token from backend:", e);
    }
    return null;
  })();
  
  return tokenFetchPromise;
}

function getAuthToken() {
  // Priority: URL param > cached token > null
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token");
  if (urlToken) return urlToken.trim();
  return (cachedAuthToken && cachedAuthToken.trim()) || "";
}

function getSettingsFromUI() {
  // Clamp values to valid ranges
  const chunkKValue = Number(chunkK.value || 10);
  const queryExpandKValue = Number(queryExpandK.value || 1);
  
  return {
    cloudBase: cloudBase.value.trim(),
    functionName: functionName.value.trim(),
    endpointPath: endpointPath.value.trim(),
    authToken: getAuthToken(),
    titleK: Number(titleK.value || 3),
    chunkK: Math.max(1, Math.min(12, chunkKValue)),
    queryExpandK: Math.max(1, Math.min(3, queryExpandKValue)),
    expandQuery: !!expandQuery.checked,
  };
}

function applySettingsToUI(s) {
  cloudBase.value = s.cloudBase ?? "";
  functionName.value = s.functionName ?? "";
  endpointPath.value = s.endpointPath ?? "";
  titleK.value = String(Number.isFinite(s.titleK) ? s.titleK : 3);
  chunkK.value = String(Number.isFinite(s.chunkK) ? s.chunkK : 10);
  queryExpandK.value = String(Number.isFinite(s.queryExpandK) ? s.queryExpandK : 1);
  expandQuery.checked = s.expandQuery ?? true;
  updateComputedUrl();
}

function loadSettings() {
  const defaults = {
    cloudBase: "https://us-central1-xixibaigao.cloudfunctions.net/",
    functionName: "chatbot-milesguo",
    endpointPath: "chatbot",
    titleK: 3,
    chunkK: 10,
    queryExpandK: 1,
    expandQuery: true,
  };

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults;
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return defaults;
  }
}

function saveSettings(s) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

function updateComputedUrl() {
  const s = getSettingsFromUI();
  const url = buildEndpointUrl(s);
  computedUrl.textContent = url || "—";
}

let inFlight = null;
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

  // Ensure token is fetched before sending request
  if (!cachedAuthToken) {
    const fetchedToken = await fetchAuthTokenFromBackend();
    if (!fetchedToken && !getAuthToken()) {
      // If no token from URL param and fetch returned null, warn user
      console.warn("No authentication token available. Backend may require authentication.");
    }
  }

  const s = getSettingsFromUI();
  const endpoint = buildEndpointUrl(s);
  if (!endpoint) {
    errorLine.textContent = "Please fill Cloud Functions base URL, function name, and endpoint path.";
    return;
  }

  addMessage({ role: "user", text });
  userInput.value = "";

  const url = new URL(endpoint);
  url.searchParams.set("txt_query", text);
  url.searchParams.set("title_k", String(s.titleK));
  url.searchParams.set("chunk_k", String(s.chunkK));
  url.searchParams.set("query_expand_k", String(s.queryExpandK));
  url.searchParams.set("expand_query", String(!!s.expandQuery));
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

  // Add thinking indicator for assistant
  const thinkingBubble = addMessage({ role: "assistant", thinking: true });

  try {
    // Get fresh token in case it was just fetched
    const authToken = getAuthToken();
    const headers = {
      Accept: "application/json",
    };
    
    // Always include Authorization header if token exists
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
      console.log("Sending request with Authorization header");
    } else {
      console.warn("No auth token available - request may fail if backend requires authentication");
    }
    
    const res = await fetch(url.toString(), {
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
        const tokenInfo = authToken ? "Token is present but invalid" : "No token provided";
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
    addMessage({ role: "assistant", text: content, sources, updateBubble: thinkingBubble });
    // Keep the last 3 Q&A pairs (6 messages) for context
    queryContext.push(`用户: ${text}`, `助手: ${content}`);
    // Keep only the last 6 messages (3 rounds of Q&A)
    if (queryContext.length > 6) {
      queryContext = queryContext.slice(-6);
    }
    setStatus("Done");
  } catch (e) {
    const msg = e?.name === "AbortError" ? "Request cancelled." : String(e?.message || e);
    addMessage({ role: "assistant", text: `Error: ${msg}`, updateBubble: thinkingBubble });
    setStatus("Error", true);
    errorLine.textContent = msg;
  } finally {
    inFlight = null;
    // If we are counting down for rate limiting, keep send disabled.
    if (!rateLimitTimer) sendBtn.disabled = false;
    cancelBtn.disabled = true;
  }
}

// Wire up UI
const cloudBase = document.getElementById("cloudBase");
const functionName = document.getElementById("functionName");
const endpointPath = document.getElementById("endpointPath");
const titleK = document.getElementById("titleK");
const chunkK = document.getElementById("chunkK");
const queryExpandK = document.getElementById("queryExpandK");
const expandQuery = document.getElementById("expandQuery");
const computedUrl = document.getElementById("computedUrl");
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
  updateComputedUrl();
});
chunkK.addEventListener("change", () => {
  const value = Number(chunkK.value);
  if (value < 1) chunkK.value = "1";
  if (value > 12) chunkK.value = "12";
  updateComputedUrl();
});

queryExpandK.addEventListener("input", () => {
  const value = Number(queryExpandK.value);
  if (value < 1) queryExpandK.value = "1";
  if (value > 3) queryExpandK.value = "3";
  updateComputedUrl();
});
queryExpandK.addEventListener("change", () => {
  const value = Number(queryExpandK.value);
  if (value < 1) queryExpandK.value = "1";
  if (value > 3) queryExpandK.value = "3";
  updateComputedUrl();
});

for (const el of [cloudBase, functionName, endpointPath, titleK, expandQuery]) {
  el.addEventListener("input", updateComputedUrl);
  el.addEventListener("change", updateComputedUrl);
}

// Auto-fetch token when base URL or function name changes
for (const el of [cloudBase, functionName]) {
  el.addEventListener("change", () => {
    cachedAuthToken = null;
    tokenFetchPromise = null;
    fetchAuthTokenFromBackend();
  });
}

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
  if (inFlight) inFlight.abort();
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
fetchAuthTokenFromBackend().then(() => {
  updateComputedUrl();
});
addMessage({
  role: "assistant",
  text:
    "Configure the Cloud Functions URL on the left, then ask a question. Auth token is automatically fetched from backend.",
});

