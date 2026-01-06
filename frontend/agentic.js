const STORAGE_KEY = "chatbot-milesguo:agentic:settings:v1";

function trimSlash(s) {
  return String(s || "").replace(/\/+$/, "");
}

function buildEndpointUrl(cloudBase) {
  const url = String(cloudBase || "").trim();
  if (!url) return "";
  // Remove trailing slash
  return trimSlash(url);
}


function setStatus(text, isError = false) {
  statusPill.textContent = text;
  statusPill.classList.toggle("danger", isError);
}

function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addMessage({ role, text, sources = null, prompt = null, querys = null, queryType = null, searchCount = null, historicalSearchOps = null, thinking = false, updateBubble = null }) {
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

    // Remove all existing details
    const existingDetails = updateBubble.querySelectorAll("details");
    existingDetails.forEach(d => d.remove());

    // Add all details for assistant messages (collapsed by default)
    if (role === "assistant") {
      if (sources && Array.isArray(sources) && sources.length > 0) {
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

      if (querys && querys.length) {
        const d = document.createElement("details");
        d.open = false;
        d.innerHTML = `<summary>Queries (${querys.length})</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em;max-height:200px;overflow:auto">${querys.map((q, i) => `${i ? 'Expanded ' + i : 'Original'}: ${q}`).join('\n')}</pre>`;
        updateBubble.appendChild(d);
      }

      if (queryType) {
        const d = document.createElement("details");
        d.open = false;
        d.innerHTML = `<summary>Query Type</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em">${queryType}</pre>`;
        updateBubble.appendChild(d);
      }

      if (searchCount !== null) {
        const d = document.createElement("details");
        d.open = false;
        d.innerHTML = `<summary>Search Count</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em">${searchCount}</pre>`;
        updateBubble.appendChild(d);
      }

      if (historicalSearchOps && Array.isArray(historicalSearchOps) && historicalSearchOps.length > 0) {
        const d = document.createElement("details");
        d.open = false;
        const opsText = historicalSearchOps.map((op, i) => {
          if (typeof op === 'object' && op !== null) {
            const opType = op.type || 'unknown';
            if (opType === 'search_general' && Array.isArray(op.query_list)) {
              return `[${i + 1}] ${opType}: ${op.query_list.join(', ')}`;
            } else if (opType === 'search_doc') {
              return `[${i + 1}] ${opType}: query="${op.query || ''}", doc_ids=[${(op.doc_ids || []).join(', ')}]`;
            } else if (opType === 'search_neighbour_chunks') {
              return `[${i + 1}] ${opType}: doc_id="${op.doc_id || ''}", chunk_id="${op.chunk_id || ''}", distance=${op.distance || 1}`;
            } else {
              return `[${i + 1}] ${opType}: ${JSON.stringify(op, null, 2)}`;
            }
          }
          return `[${i + 1}] ${String(op)}`;
        }).join('\n');
        d.innerHTML = `<summary>Historical Search Ops (${historicalSearchOps.length})</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em;max-height:300px;overflow:auto">${opsText}</pre>`;
        updateBubble.appendChild(d);
      }

      if (prompt) {
        const d = document.createElement("details");
        d.open = false;
        d.innerHTML = `<summary>Prompt</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.85em;max-height:400px;overflow:auto;background:#f5f5f5">${prompt}</pre>`;
        updateBubble.appendChild(d);
      }
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
      const score = s.score != null ? Number(s.score).toFixed(4) : "";
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

  if (role === "assistant") {
    if (querys && querys.length) {
      const d = document.createElement("details");
      d.open = false;
      d.innerHTML = `<summary>Queries (${querys.length})</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em;max-height:200px;overflow:auto">${querys.map((q, i) => `${i ? 'Expanded ' + i : 'Original'}: ${q}`).join('\n')}</pre>`;
      bubble.appendChild(d);
    }
    if (queryType) {
      const d = document.createElement("details");
      d.open = false;
      d.innerHTML = `<summary>Query Type</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em">${queryType}</pre>`;
      bubble.appendChild(d);
    }
    if (searchCount !== null) {
      const d = document.createElement("details");
      d.open = false;
      d.innerHTML = `<summary>Search Count</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em">${searchCount}</pre>`;
      bubble.appendChild(d);
    }
    if (historicalSearchOps && Array.isArray(historicalSearchOps) && historicalSearchOps.length > 0) {
      const d = document.createElement("details");
      d.open = false;
      const opsText = historicalSearchOps.map((op, i) => {
        if (typeof op === 'object' && op !== null) {
          const opType = op.type || 'unknown';
          if (opType === 'search_general' && Array.isArray(op.query_list)) {
            return `[${i + 1}] ${opType}: ${op.query_list.join(', ')}`;
          } else if (opType === 'search_doc') {
            return `[${i + 1}] ${opType}: query="${op.query || ''}", doc_ids=[${(op.doc_ids || []).join(', ')}]`;
          } else if (opType === 'search_neighbour_chunks') {
            return `[${i + 1}] ${opType}: doc_id="${op.doc_id || ''}", chunk_id="${op.chunk_id || ''}", distance=${op.distance || 1}`;
          } else {
            return `[${i + 1}] ${opType}: ${JSON.stringify(op, null, 2)}`;
          }
        }
        return `[${i + 1}] ${String(op)}`;
      }).join('\n');
      d.innerHTML = `<summary>Historical Search Ops (${historicalSearchOps.length})</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.9em;max-height:300px;overflow:auto">${opsText}</pre>`;
      bubble.appendChild(d);
    }
    if (prompt) {
      const d = document.createElement("details");
      d.open = false;
      d.innerHTML = `<summary>Prompt</summary><pre style="padding:8px;white-space:pre-wrap;font-size:0.85em;max-height:400px;overflow:auto;background:#f5f5f5">${prompt}</pre>`;
      bubble.appendChild(d);
    }
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
      // Build the token URL by replacing the last path segment with "token"
      const baseUrl = (cloudBase?.value || "").trim();
      if (!baseUrl) {
        console.warn("Cloud Functions URL is empty.");
        return null;
      }
      
      // Validate URL format
      let url;
      try {
        url = new URL(baseUrl);
      } catch (e) {
        console.error("Invalid Cloud Functions URL format:", e, "URL was:", baseUrl);
        return null;
      }
      
      // Build token URL by replacing the last path segment with "token"
      let tokenUrl;
      try {
        const pathSegments = url.pathname.split("/").filter(Boolean);
        // Replace the last segment (endpoint path) with "token"
        if (pathSegments.length > 0) {
          pathSegments[pathSegments.length - 1] = "token";
          url.pathname = "/" + pathSegments.join("/");
        } else {
          // If URL has no path, append /token
          url.pathname = "/token";
        }
        tokenUrl = url.toString();
        console.log("Cloud Functions URL:", baseUrl);
        console.log("Constructed token URL:", tokenUrl);
      } catch (e) {
        console.warn("Error constructing token URL:", e, "URL was:", baseUrl);
        return null;
      }
      if (!tokenUrl) {
        console.warn("Token URL is empty (check Cloud Functions URL).");
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
  const maxIterValue = Number(maxIter.value || 1);
  
  return {
    cloudBase: cloudBase.value.trim(),
    authToken: getAuthToken(),
    titleK: Number(titleK.value || 3),
    chunkK: Math.max(1, Math.min(12, chunkKValue)),
    queryExpandK: Math.max(1, Math.min(3, queryExpandKValue)),
    chunkIndex: chunkIndex.value.trim() || null,
    maxIter: Math.max(1, Math.min(5, maxIterValue)),
  };
}

function applySettingsToUI(s) {
  cloudBase.value = s.cloudBase ?? "";
  titleK.value = String(Number.isFinite(s.titleK) ? s.titleK : 3);
  chunkK.value = String(Number.isFinite(s.chunkK) ? s.chunkK : 12);
  queryExpandK.value = String(Number.isFinite(s.queryExpandK) ? s.queryExpandK : 1);
  chunkIndex.value = s.chunkIndex ?? "";
  maxIter.value = String(Number.isFinite(s.maxIter) ? s.maxIter : 2);
}

function loadSettings() {
  const defaults = {
    cloudBase: "https://us-central1-xixibaigao.cloudfunctions.net/chatbot-milesguo/agentic_rag",
    titleK: 3,
    chunkK: 12,
    queryExpandK: 1,
    chunkIndex: "",
    maxIter: 2,
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

  // Use the full URL directly (user can specify complete endpoint like /agentic_rag)
  const url = new URL(endpoint);
  url.searchParams.set("txt_query", text);
  url.searchParams.set("title_k", String(s.titleK));
  url.searchParams.set("chunk_k", String(s.chunkK));
  url.searchParams.set("query_expand_k", String(s.queryExpandK));
  url.searchParams.set("max_iter", String(s.maxIter));
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
    const prompt = data?.prompt ?? null;
    const querys = Array.isArray(data?.querys) ? data.querys : null;
    const queryType = data?.query_type ?? null;
    const searchCount = data?.search_count ?? null;
    const historicalSearchOps = Array.isArray(data?.historical_search_ops) ? data.historical_search_ops : null;
    addMessage({ role: "assistant", text: content, sources, prompt, querys, queryType, searchCount, historicalSearchOps, updateBubble: thinkingBubble });
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
const titleK = document.getElementById("titleK");
const chunkK = document.getElementById("chunkK");
const queryExpandK = document.getElementById("queryExpandK");
const chunkIndex = document.getElementById("chunkIndex");
const maxIter = document.getElementById("maxIter");
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

maxIter.addEventListener("input", () => {
  const value = Number(maxIter.value);
  if (value < 1) maxIter.value = "1";
  if (value > 5) maxIter.value = "5";
});
maxIter.addEventListener("change", () => {
  const value = Number(maxIter.value);
  if (value < 1) maxIter.value = "1";
  if (value > 5) maxIter.value = "5";
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
fetchAuthTokenFromBackend();
addMessage({
  role: "assistant",
  text: "请提问",
});

