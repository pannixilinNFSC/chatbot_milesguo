// Shared frontend utilities for chatbot pages.
// Motivation: avoid duplicated logic between standard RAG and Agentic RAG UIs.

// Remove trailing slashes from a URL-like string.
function trimSlash(s) {
  return String(s || "").replace(/\/+$/, "");
}

// Normalize endpoint URL from the Cloud Functions base.
function buildEndpointUrl(cloudBase) {
  const url = String(cloudBase || "").trim();
  if (!url) return "";
  return trimSlash(url);
}

// Update the status pill with optional error styling.
function setStatus(text, isError = false) {
  statusPill.textContent = text;
  statusPill.classList.toggle("danger", isError);
}

// Format current time for chat message metadata.
function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Typewriter effect for assistant messages.
async function typewriterEffect(element, text, speed = 20) {
  element.textContent = "";
  element.classList.add("typing");

  for (let i = 0; i < text.length; i++) {
    element.textContent += text[i];
    // Scroll to bottom as content is typed
    messages.scrollTop = messages.scrollHeight;
    // Small delay between characters
    // eslint-disable-next-line no-await-in-loop
    await new Promise((resolve) => setTimeout(resolve, speed));
  }

  element.classList.remove("typing");
}

// Copy text to clipboard with a fallback for older browsers.
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand("copy");
      document.body.removeChild(textArea);
      return true;
    } catch (e) {
      document.body.removeChild(textArea);
      return false;
    }
  }
}

// Shared auth token cache across pages in this frontend.
let cachedAuthToken = null;
let tokenFetchPromise = null;

// Fetch auth token from backend by rewriting the Cloud Functions URL path to /token.
async function fetchAuthTokenFromBackend() {
  if (tokenFetchPromise) return tokenFetchPromise;

  tokenFetchPromise = (async () => {
    try {
      const baseUrl = (cloudBase?.value || "").trim();
      if (!baseUrl) {
        console.warn("Cloud Functions URL is empty.");
        return null;
      }

      let url;
      try {
        url = new URL(baseUrl);
      } catch (e) {
        console.error("Invalid Cloud Functions URL format:", e, "URL was:", baseUrl);
        return null;
      }

      let tokenUrl;
      try {
        const pathSegments = url.pathname.split("/").filter(Boolean);
        if (pathSegments.length > 0) {
          pathSegments[pathSegments.length - 1] = "token";
          url.pathname = "/" + pathSegments.join("/");
        } else {
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
          cachedAuthToken = cachedAuthToken.trim();
          console.log("Auth token fetched successfully");
        } else {
          console.warn("Auth token is null - authentication may not be enabled on backend");
        }
        return cachedAuthToken;
      }
      console.warn(`Failed to fetch auth token: ${res.status} ${res.statusText}`);
    } catch (e) {
      console.warn("Failed to fetch auth token from backend:", e);
    }
    return null;
  })();

  return tokenFetchPromise;
}

// Get auth token from URL param or cached backend token.
function getAuthToken() {
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token");
  if (urlToken) return urlToken.trim();
  return (cachedAuthToken && cachedAuthToken.trim()) || "";
}


