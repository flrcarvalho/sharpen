// Config compartilhada (popup + background). Ponto único de verdade da URL da API.
// Host canônico do Railway = www.sharpen.bet (o apex sharpen.bet dá 301 na GoDaddy,
// e redirect em POST pode derrubar o corpo → sempre falar com o www).
const API_BASE_PADRAO = "https://www.sharpen.bet";

// Lê a base da API (permite override em storage para testar contra um preview).
async function getApiBase() {
  const { apiBase } = await chrome.storage.local.get("apiBase");
  return (apiBase || API_BASE_PADRAO).replace(/\/+$/, "");
}
