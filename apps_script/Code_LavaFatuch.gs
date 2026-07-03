// ============================================================
//  BETTING DASHBOARD — Apps Script (planilha do FATUCH / operador LavaFatuch)
//  Cole este código em: Extensões > Apps Script > Code.gs  (na planilha DELE)
//
//  Espelha o Code.gs v6.1 do dashboard (mesma arquitetura de cache no
//  Drive + gatilho de 30 min + leitura via Sheets API sem recálculo).
//  O CONTRATO DE SAÍDA é idêntico ao usado pelo /dashboard/data do app.
//
//  DIFERENÇAS vs a planilha original (layout do Fatuch):
//    • Os dados começam na LINHA 4 (cabeçalho na 3) → range A4:N.
//    • Há uma coluna "Tipo" (H) que empurra Stake→I, Odd→J, W/L→K.
//    • O P/L em R$ (fonte de verdade) fica na coluna N ("P/L (R$)").
//    • Se o P/L (R$) não vier como número nativo, o lucro é DERIVADO de
//      stake×odd×resultado (calcular_pl do app) em vez de descartar a linha.
//
//  PASSO A PASSO DE INSTALAÇÃO:
//    1) Cole este arquivo inteiro no Code.gs da planilha do Fatuch.
//    2) Editor > Serviços (＋) > "Google Sheets API" > Adicionar.
//       O identificador TEM que ficar como "Sheets".
//    3) Rode rebuildCache() uma vez à mão (autoriza os acessos).
//    4) Acionadores (relógio) > novo gatilho: função rebuildCache,
//       origem "Baseado em tempo", a cada 30 minutos.
//    5) Implantar > Nova implantação > Tipo "App da Web":
//         - Executar como: EU (dono da planilha)
//         - Quem tem acesso: QUALQUER PESSOA
//       Copie a URL /exec e mande para o Feca (vira PLANILHA_LAVAFATUCH_URL).
// ============================================================

const SHEET_NAME     = "BASE";   // <-- CONFIRMAR o nome da aba (gid=0)
const SPREADSHEET_ID = "1XCtZoBnBeq6KSOiwjmAb780Z9FfSsMsr9fjVYMQGa6Y";

// Colunas 1-indexadas na planilha do Fatuch:
const COL_DATA      = 1;   // A
const COL_ESPORTE   = 2;   // B
const COL_TIPSTER   = 3;   // C
const COL_CASA      = 4;   // D
const COL_PARCEIRO  = 5;   // E
const COL_APOSTA    = 6;   // F
const COL_DESCRICAO = 7;   // G
// (H = "Tipo" — ignorado)
const COL_STAKE     = 9;   // I — Stake (R$)
const COL_ODD       = 10;  // J — Odd
const COL_RESULTADO = 11;  // K — W/L
const COL_PL        = 14;  // N — P/L (R$), fonte de verdade

// Range lido: da linha 4 (1ª aposta) até a coluna N.
const RANGE = SHEET_NAME + "!A4:N";

// Nome do arquivo de cache no Google Drive (raiz do Meu Drive).
const CACHE_FILE_NAME = "betting-dashboard-cache-fatuch.json";

// ------------------------------------------------------------
// Entry point GET
//   • normal           → devolve o JSON já pronto do cache (rápido)
//   • ?refresh=1        → reconstrói na hora e devolve fresco (lento)
//   • cache inexistente → fallback: lê ao vivo (lento, só na 1ª vez)
// ------------------------------------------------------------
function doGet(e) {
  const output = ContentService.createTextOutput();
  output.setMimeType(ContentService.MimeType.JSON);

  const forceRefresh = e && e.parameter && e.parameter.refresh === "1";

  try {
    if (forceRefresh) {
      output.setContent(rebuildCache());
      return output;
    }
    const cached = readCache();
    if (cached) {
      output.setContent(cached);
      return output;
    }
    output.setContent(rebuildCache());
  } catch (err) {
    output.setContent(JSON.stringify({ ok: false, error: err.message }));
  }
  return output;
}

// ------------------------------------------------------------
// rebuildCache — monta o JSON pronto, grava no Drive e devolve.
// É a função do gatilho agendado (a cada 30 min).
// ------------------------------------------------------------
function rebuildCache() {
  const t0 = Date.now();
  const data = getData();
  const payload = JSON.stringify({
    ok: true,
    data: data,
    builtAt: new Date().toISOString(),
    count: data.length,
  });
  writeCache(payload);
  Logger.log("rebuildCache: " + data.length + " apostas em " +
             ((Date.now() - t0) / 1000).toFixed(1) + "s — " +
             (payload.length / 1024 / 1024).toFixed(2) + " MB");
  return payload;
}

// ------------------------------------------------------------
// Helpers de cache em arquivo do Drive
// ------------------------------------------------------------
function _getCacheFile() {
  const it = DriveApp.getFilesByName(CACHE_FILE_NAME);
  return it.hasNext() ? it.next() : null;
}
function writeCache(content) {
  const f = _getCacheFile();
  if (f) { f.setContent(content); return f; }
  return DriveApp.createFile(CACHE_FILE_NAME, content, "application/json");
}
function readCache() {
  const f = _getCacheFile();
  return f ? f.getBlob().getDataAsString() : null;
}

// ------------------------------------------------------------
// Helpers de leitura
// ------------------------------------------------------------

// Célula segura: arrays da Sheets API são "ragged" (linhas com
// células finais vazias vêm mais curtas). Evita "undefined".
function _cell(row, i) {
  return (i < row.length && row[i] != null) ? row[i] : "";
}

// Serial do Sheets (dias desde 1899-12-30) → "yyyy-MM-dd" (UTC, sem shift de fuso).
function _serialToISO(serial) {
  const n = Math.floor(serial);
  const d = new Date((n - 25569) * 86400000);
  const m   = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return d.getUTCFullYear() + "-" + m + "-" + day;
}

// Número tolerante: aceita number nativo ou string "1.234,56"/"1,31".
function _num(v) {
  if (typeof v === 'number') return v;
  const s = String(v).replace(/[R$\s]/g, "").replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".");
  const n = parseFloat(s);
  return isNaN(n) ? 0 : n;
}

// Deriva o lucro (P/L em R$) igual ao calcular_pl do app, quando a planilha
// não entrega P/L (R$) como número. Retorno = valor − stake.
function _derivarLucro(stake, odd, resultado) {
  switch (resultado) {
    case "W":  return stake * odd - stake;
    case "L":  return -stake;
    case "V":  return 0;
    case "HW": return (stake / 2) * odd + stake / 2 - stake;
    case "HL": return -stake / 2;
    default:   return null;
  }
}

// ------------------------------------------------------------
// Lê e normaliza os dados — via Sheets API (sem recálculo).
// Contrato de saída idêntico ao /dashboard/data do app.
// ------------------------------------------------------------
function getData() {
  const resp = Sheets.Spreadsheets.Values.get(
    SPREADSHEET_ID,
    RANGE,
    { valueRenderOption: "UNFORMATTED_VALUE", dateTimeRenderOption: "SERIAL_NUMBER" }
  );

  const values = resp.values || [];
  const rows   = [];

  values.forEach(row => {

    // ── Resultado — única validação obrigatória (aceita "w" minúsculo) ──
    const resultado = String(_cell(row, COL_RESULTADO - 1)).trim().toUpperCase();
    if (!["W","L","V","HW","HL"].includes(resultado)) return;

    // ── Stake ───────────────────────────────────────────────
    const stake = _num(_cell(row, COL_STAKE - 1));
    if (stake <= 0) return;

    // ── Odd ─────────────────────────────────────────────────
    const odd = _num(_cell(row, COL_ODD - 1));

    // ── Lucro (P/L R$) — planilha é a fonte de verdade; deriva se faltar ──
    const rawPL = _cell(row, COL_PL - 1);
    let lucro = (typeof rawPL === 'number') ? parseFloat(rawPL.toFixed(2))
                                            : _derivarLucro(stake, odd, resultado);
    if (lucro === null || isNaN(lucro)) return;
    lucro = parseFloat(Number(lucro).toFixed(2));

    // ── Data ────────────────────────────────────────────────
    const rawData = _cell(row, COL_DATA - 1);
    let dataISO = "";
    if (typeof rawData === 'number' && rawData > 0) {
      dataISO = _serialToISO(rawData);
    } else {
      const parts = String(rawData).split("/");
      if (parts.length === 3) {
        dataISO = `${parts[2]}-${parts[1].padStart(2,"0")}-${parts[0].padStart(2,"0")}`;
      }
    }
    if (!dataISO) return;

    // ── Parceiro (conta [fornecedor]) ───────────────────────
    const parceiroRaw = String(_cell(row, COL_PARCEIRO - 1)).trim();
    let conta = parceiroRaw, fornecedor = "";
    const m = parceiroRaw.match(/^(.+?)\s*\[(.+?)\]$/);
    if (m) { conta = m[1].trim(); fornecedor = m[2].trim(); }

    rows.push({
      data:      dataISO,
      esporte:   String(_cell(row, COL_ESPORTE   - 1)).trim(),
      tipster:   String(_cell(row, COL_TIPSTER   - 1)).trim(),
      casa:      String(_cell(row, COL_CASA      - 1)).trim(),
      parceiro:  parceiroRaw,
      conta,
      fornecedor,
      aposta:    String(_cell(row, COL_APOSTA    - 1)).trim(),
      descricao: String(_cell(row, COL_DESCRICAO - 1)).trim(),
      stake,
      odd,
      resultado,
      lucro,
    });
  });

  return rows;
}

// ------------------------------------------------------------
// Teste — mostra o tempo de leitura e os totais (rode à mão)
// ------------------------------------------------------------
function testar() {
  const t0 = Date.now();
  const rows = getData();
  const segs = ((Date.now() - t0) / 1000).toFixed(1);
  const lucroTotal = rows.reduce((a, r) => a + r.lucro, 0);
  const stakeTotal = rows.reduce((a, r) => a + r.stake, 0);
  Logger.log("Leitura via Sheets API: " + segs + "s");
  Logger.log("Total apostas: " + rows.length);
  Logger.log("Lucro total: R$ " + lucroTotal.toFixed(2));
  Logger.log("Stake total: R$ " + stakeTotal.toFixed(2));
  Logger.log("ROI: " + (lucroTotal / stakeTotal * 100).toFixed(2) + "%");
}
