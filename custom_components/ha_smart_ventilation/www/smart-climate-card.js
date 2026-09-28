/*
 * Smart Climate - eigenständige Lovelace-Custom-Card.
 *
 * Parallel zur README-Markdown/Jinja-Karte nutzbar (siehe CLAUDE.md) - liest
 * exakt dieselben binary_sensor-Attribute (offene_gruende, schliessgrund_live
 * usw., siehe binary_sensor.py:_live_reasons()) und bildet dieselbe
 * Farb-/Prioritätslogik nach, aber als echtes JS-Custom-Element statt
 * Jinja-Vorlage - dadurch keine Home-Assistant-Jinja-Sandbox-Einschränkungen
 * (Lektion 4-7) und volle CSS-Kontrolle statt der <font>/<strong>-Notlösung
 * aus Lektion 5.
 *
 * Eigene, von der Jinja-Karte unabhängige Versionierung (siehe unten).
 */

const CARD_VERSION = 1;

const GRUND_TEXT = {
  temp: "Temperatur",
  humidity: "Luftfeuchtigkeit",
  co2: "CO2",
  frost: "Frostschutz",
  heat: "Hitzeschutz",
  duration: "Winter-Höchstdauer",
  outdoor_warmer: "Außen wärmer",
  outdoor_wetter: "Außen feuchter",
};

const HEATING_MODE_LABEL = {
  comfort: { icon: "🔴", text: "Komfort" },
  night: { icon: "🟡", text: "Eco (Nacht)" },
  building_protection: { icon: "🔵", text: "Gebäudeschutz" },
  standby: { icon: "🟠", text: "Standby" },
};

function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function localDateStr(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function localDateTimeMinuteStr(date) {
  return `${localDateStr(date)} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

function shortTimeStr(date, todayStr) {
  const hhmm = `${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
  if (localDateStr(date) === todayStr) return hhmm;
  return `${pad2(date.getDate())}.${pad2(date.getMonth() + 1)}. ${hhmm}`;
}

function roundStr(value, decimals) {
  if (value === null || value === undefined) return null;
  const num = Number(value);
  if (Number.isNaN(num)) return null;
  return num.toFixed(decimals);
}

function fmtDuration(minutes) {
  if (minutes === null || minutes === undefined) return "–";
  const m = Math.max(0, Math.floor(minutes));
  if (m < 60) return `${m} Min`;
  return `${Math.floor(m / 60)}h ${m % 60} Min`;
}

function has(attrs, key) {
  return Object.prototype.hasOwnProperty.call(attrs, key);
}

class SmartClimateCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 8;
  }

  connectedCallback() {
    if (this._hass) this._render();
  }

  _entityIds() {
    const states = this._hass.states;
    if (this._config.entities && this._config.entities.length) {
      return this._config.entities.filter((id) => states[id]);
    }
    return Object.keys(states).filter(
      (id) =>
        id.startsWith("binary_sensor.") &&
        states[id].attributes &&
        has(states[id].attributes, "raum")
    );
  }

  _render() {
    if (!this._hass) return;
    const hass = this._hass;
    const states = hass.states;
    const entityIds = this._entityIds();
    const today = new Date();
    const todayStr = localDateStr(today);

    if (!this._card) {
      this._card = document.createElement("ha-card");
      this._style = document.createElement("style");
      this._style.textContent = SmartClimateCard._css();
      this._content = document.createElement("div");
      this._content.className = "smart-climate-card-content";
      this._card.appendChild(this._style);
      this._card.appendChild(this._content);
      this.appendChild(this._card);
    }

    if (!entityIds.length) {
      this._content.innerHTML =
        '<div class="empty">Keine Räume gefunden (kein binary_sensor mit "raum"-Attribut).</div>';
      return;
    }

    // Pass 1: Fenster-Zeitstempel sammeln (für den "Massen-Reset"-Filter,
    // siehe README/Jinja-Karte - erkennt einen Home-Assistant-Neustart, bei
    // dem mehrere Fensterkontakte gleichzeitig neu registriert wurden).
    const windowTimes = [];
    for (const id of entityIds) {
      const s = states[id];
      const a = s.attributes;
      const windowEntity = a.fensterkontakt_entity;
      if (windowEntity && states[windowEntity]) {
        const w = states[windowEntity].state;
        if (w === "on" || w === "off") {
          windowTimes.push(
            localDateTimeMinuteStr(new Date(states[windowEntity].last_changed))
          );
        }
      }
    }

    let green = 0;
    let orange = 0;
    let red = 0;
    let version = null;
    let summerMode = null;
    const entries = [];

    const sorted = [...entityIds].sort((idA, idB) =>
      String(states[idA].attributes.raum).localeCompare(
        String(states[idB].attributes.raum)
      )
    );

    for (const id of sorted) {
      const s = states[id];
      const a = s.attributes;

      const noWindow = has(a, "hat_fenster") && a.hat_fenster === false;
      const openReasons = a.offene_gruende || [];
      const openLabel = openReasons.map((c) => GRUND_TEXT[c] || c).join(", ");
      const liveGrundOpen = openReasons.length ? openReasons[0] : "";
      const liveGrundClose = a.schliessgrund_live || "";
      const highlightCode = s.state === "on" ? liveGrundOpen : liveGrundClose;
      const hasLiveReason = highlightCode !== "";

      const windowEntity = a.fensterkontakt_entity || "";
      let windowStateText = "–";
      let windowChangedTime = "–";
      const co2CloseException = s.state === "off" && highlightCode === "co2";
      const comfortCloseResolvedException =
        s.state === "off" &&
        ["humidity", "temp", "outdoor_warmer", "outdoor_wetter"].includes(highlightCode);
      const noWindowResolved = noWindow && comfortCloseResolvedException;

      let matchIcon = !hasLiveReason || co2CloseException || noWindowResolved
        ? "🟢"
        : noWindow
        ? "🟠"
        : "🔴";
      let highlightOk = false;

      if (windowEntity && states[windowEntity]) {
        const w = states[windowEntity].state;
        windowStateText = w === "on" ? "geöffnet" : w === "off" ? "geschlossen" : "unbekannt";
        if (w === "on" || w === "off") {
          const windowDt = new Date(states[windowEntity].last_changed);
          const windowKey = localDateTimeMinuteStr(windowDt);
          const massReset = windowTimes.filter((t) => t === windowKey).length >= 3;
          windowChangedTime = massReset ? "–" : shortTimeStr(windowDt, todayStr);
        }
        if (!noWindow && hasLiveReason && !co2CloseException && (w === "on" || w === "off")) {
          const isMatch = (s.state === "on") === (w === "on");
          matchIcon = isMatch ? (comfortCloseResolvedException ? "🟢" : "🟠") : "🔴";
          highlightOk = isMatch;
        }
      }

      if (version === null && has(a, "integration_version")) version = a.integration_version;
      if (summerMode === null && has(a, "sommermodus_an")) summerMode = a.sommermodus_an;

      if (matchIcon === "🟢") green += 1;
      else if (matchIcon === "🟠") orange += 1;
      else if (matchIcon === "🔴") red += 1;

      const highlightClass =
        co2CloseException || (comfortCloseResolvedException && highlightOk) || noWindowResolved
          ? "hl-green"
          : noWindow || highlightOk
          ? "hl-orange"
          : "hl-red";

      const statusText = hasLiveReason ? (s.state === "on" ? "Öffnen" : "Schließen") : "–";
      let changedTime = "–";
      if (hasLiveReason && a.letzter_wechsel) {
        changedTime = shortTimeStr(new Date(a.letzter_wechsel), todayStr);
      }

      const highlightTemp = s.state === "on" ? openReasons.includes("temp") : highlightCode === "temp";
      const highlightHum = s.state === "on" ? openReasons.includes("humidity") : highlightCode === "humidity";
      const highlightCo2 = s.state === "on" ? openReasons.includes("co2") : highlightCode === "co2";

      const wrap = (text, on) => (on ? `<span class="${highlightClass}">${text}</span>` : text);

      const tempVal = wrap(
        a.innentemperatur !== undefined && a.innentemperatur !== null
          ? `${roundStr(a.innentemperatur, 1)} °C`
          : "–",
        highlightTemp
      );
      const outdoorTempDefined = has(a, "aussentemperatur") && a.aussentemperatur !== null;
      const outdoorTempVal = wrap(
        outdoorTempDefined ? `${roundStr(a.aussentemperatur, 1)} °C` : "–",
        ["frost", "heat", "outdoor_warmer"].includes(highlightCode)
      );
      const outdoorHumDefined = has(a, "aussen_luftfeuchtigkeit") && a.aussen_luftfeuchtigkeit !== null;
      const outdoorHumVal = outdoorHumDefined ? roundStr(a.aussen_luftfeuchtigkeit, 0) : "–";

      let humRow = "";
      if (has(a, "luftfeuchtigkeit")) {
        const humVal = wrap(
          a.luftfeuchtigkeit !== null ? `${roundStr(a.luftfeuchtigkeit, 0)} %` : "–",
          highlightHum
        );
        const lo = Math.min(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
        const hi = Math.max(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
        humRow = `<tr><td>Luftfeuchtigkeit</td><td>${humVal}</td><td>${outdoorHumVal} %</td><td>${Math.round(lo)} - ${Math.round(hi)} %</td></tr>`;
      }

      let co2Row = "";
      if (has(a, "co2")) {
        const co2Val = wrap(a.co2 !== null ? `${roundStr(a.co2, 0)} ppm` : "–", highlightCo2);
        const lo = Math.min(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        const hi = Math.max(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        co2Row = `<tr><td>CO2</td><td>${co2Val}</td><td>–</td><td>${Math.round(lo)} - ${Math.round(hi)} ppm</td></tr>`;
      }

      let absRow = "";
      if (has(a, "luftfeuchtigkeit")) {
        const absIn =
          has(a, "absolute_luftfeuchtigkeit") && a.absolute_luftfeuchtigkeit !== null
            ? `${a.absolute_luftfeuchtigkeit} g/m³`
            : "–";
        let absOut =
          has(a, "aussen_absolute_luftfeuchtigkeit") && a.aussen_absolute_luftfeuchtigkeit !== null
            ? `${a.aussen_absolute_luftfeuchtigkeit} g/m³`
            : "–";
        absOut = wrap(absOut, highlightCode === "outdoor_wetter");
        absRow = `<tr><td>Abs. Luftfeuchtigkeit</td><td>${absIn}</td><td>${absOut}</td><td>–</td></tr>`;
      }

      // Geräte-Tabelle
      let deviceRows = "";
      if (has(a, "luftentfeuchter_an")) {
        let name = `${a.luftentfeuchter_an ? "🔴" : "⚫"}&nbsp;Luftentfeuchter`;
        if (has(a, "luftentfeuchter_tank_fehler")) {
          name += `<br>${a.luftentfeuchter_tank_fehler ? "🔴" : "🟢"}&nbsp;Wassertank`;
        }
        let laufzeit = "–";
        if (a.luftentfeuchter_an && a.luftentfeuchter_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.luftentfeuchter_seit).getTime()) / 60000);
        } else if (has(a, "luftentfeuchter_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.luftentfeuchter_letzte_laufzeit);
        }
        const grund = has(a, "luftentfeuchter_grund") ? esc(a.luftentfeuchter_grund) : "–";
        deviceRows += `<tr><td>${name}</td><td class="center">${laufzeit}</td><td>${grund}</td></tr>`;
      }
      if (has(a, "klimaanlage_an")) {
        const name = `${a.klimaanlage_an ? "🔴" : "⚫"}&nbsp;Klimaanlage`;
        let laufzeit = "–";
        if (a.klimaanlage_an && a.klimaanlage_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.klimaanlage_seit).getTime()) / 60000);
        } else if (has(a, "klimaanlage_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.klimaanlage_letzte_laufzeit);
        }
        const grund = has(a, "klimaanlage_grund") ? esc(a.klimaanlage_grund) : "–";
        deviceRows += `<tr><td>${name}</td><td class="center">${laufzeit}</td><td>${grund}</td></tr>`;
      }
      if (has(a, "heizung_an")) {
        let name = `${a.heizung_an ? "🔴" : "⚫"}&nbsp;Heizung`;
        const modeInfo = has(a, "heizung_modus") ? HEATING_MODE_LABEL[a.heizung_modus] : undefined;
        if (modeInfo) name += `<br>${modeInfo.icon}&nbsp;${modeInfo.text}`;
        let laufzeit = "–";
        if (a.heizung_an && a.heizung_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.heizung_seit).getTime()) / 60000);
        } else if (has(a, "heizung_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.heizung_letzte_laufzeit);
        }
        let grund = has(a, "heizung_grund") ? esc(a.heizung_grund) : "–";
        if (has(a, "heizung_zieltemperatur") && a.heizung_zieltemperatur !== null) {
          grund += ` (${roundStr(a.heizung_zieltemperatur, 1)} °C)`;
        }
        deviceRows += `<tr><td>${name}</td><td class="center">${laufzeit}</td><td>${grund}</td></tr>`;
      }
      if (has(a, "duschen_erkannt")) {
        const name = `${a.duschen_erkannt ? "🟢" : "⚫"}&nbsp;Dusche`;
        let laufzeit = "–";
        if (a.duschen_erkannt && a.dusche_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.dusche_seit).getTime()) / 60000);
        } else if (has(a, "dusche_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.dusche_letzte_laufzeit);
        }
        const grund = a.duschen_erkannt ? "Luftfeuchtigkeit steigt schnell" : "–";
        deviceRows += `<tr><td>${name}</td><td class="center">${laufzeit}</td><td>${grund}</td></tr>`;
      }
      const deviceTable = deviceRows
        ? `<table class="values"><thead><tr><th>Gerät</th><th>Laufzeit</th><th>Grund</th></tr></thead><tbody>${deviceRows}</tbody></table>`
        : "";

      const grundLabel =
        s.state === "on"
          ? openLabel || "–"
          : highlightCode
          ? GRUND_TEXT[highlightCode] || highlightCode
          : "–";

      const empfehlungText = hasLiveReason ? wrap(statusText, true) : statusText;

      let empfTable = "";
      if (!noWindow) {
        empfTable =
          `<table class="values"><thead><tr><th>Fenster</th><th>Empfehlung</th><th>Auslöser</th><th>Uhrzeit</th></tr></thead><tbody>` +
          `<tr><td>${windowStateText}</td><td>–</td><td>–</td><td>${windowChangedTime}</td></tr>`;
        if (hasLiveReason) {
          empfTable += `<tr><td>–</td><td>${empfehlungText}</td><td>${esc(grundLabel)}</td><td>${changedTime}</td></tr>`;
        }
        empfTable += "</tbody></table>";
      }

      const tempLo = Math.min(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const tempHi = Math.max(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const valuesTable =
        `<table class="values"><thead><tr><th>Messwert</th><th>Innen</th><th>Außen</th><th>Normalbereich</th></tr></thead><tbody>` +
        `<tr><td>Temperatur</td><td>${tempVal}</td><td>${outdoorTempVal}</td><td>${tempLo} - ${tempHi} °C</td></tr>` +
        `${humRow}${absRow}${co2Row}</tbody></table>`;

      const n1Status = has(a, "sprachausgabe_aktiv") ? "🟢" : "⚫";
      const n1Ziel = has(a, "sprachausgabe_lautsprecher") ? esc(a.sprachausgabe_lautsprecher.join(", ")) : "–";
      const n2Status = has(a, "app_aktiv") ? "🟢" : "⚫";
      const n2Ziel = has(a, "app_ziele") ? esc(a.app_ziele.join(", ")) : "–";
      const n3Status = has(a, "persistent_aktiv") ? "🟢" : "⚫";
      const notifyTable =
        `<details><summary><strong>Benachrichtigungen</strong></summary>` +
        `<table class="values"><thead><tr><th>Benachrichtigung</th><th>Status</th><th>Ziel(e)</th></tr></thead><tbody>` +
        `<tr><td>Sprachausgabe</td><td class="center">${n1Status}</td><td>${n1Ziel}</td></tr>` +
        `<tr><td>App-Benachrichtigung</td><td class="center">${n2Status}</td><td>${n2Ziel}</td></tr>` +
        `<tr><td>Persistente Benachrichtigung</td><td class="center">${n3Status}</td><td>–</td></tr>` +
        `</tbody></table></details>`;

      const header = `<h3>${matchIcon} ${esc(a.raum)}</h3>`;
      let body = empfTable;
      body += valuesTable;
      if (deviceTable) body += deviceTable;
      body += notifyTable;

      const colorRank = matchIcon === "🔴" ? 0 : matchIcon === "🟠" ? 1 : 2;
      entries.push({
        sortKey: `${colorRank}${a.raum}`,
        html: `<div class="room">${header}${body}</div>`,
      });
    }

    entries.sort((x, y) => x.sortKey.localeCompare(y.sortKey));

    const overviewCols = [];
    const overviewVals = [];
    overviewCols.push("🟢", "🟠", "🔴");
    overviewVals.push(String(green), String(orange), String(red));
    if (summerMode !== null) {
      overviewCols.push("Modus");
      overviewVals.push(summerMode ? "☀️ Sommer" : "❄️ Winter");
    }
    if (version !== null) {
      overviewCols.push("Integration");
      overviewVals.push(esc(version));
    }
    overviewCols.push("Karte");
    overviewVals.push(String(CARD_VERSION));

    const overviewTable =
      `<table class="overview"><thead><tr>${overviewCols
        .map((c) => `<th>${c}</th>`)
        .join("")}</tr></thead><tbody><tr>${overviewVals
        .map((v) => `<td>${v}</td>`)
        .join("")}</tr></tbody></table>`;

    const roomsHtml = entries.map((e) => e.html).join('<hr class="room-sep">');

    this._content.innerHTML = `${overviewTable}<hr class="room-sep">${roomsHtml}`;
  }

  static _css() {
    return `
      .smart-climate-card-content { padding: 16px; }
      table.overview, table.values { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
      table.overview th, table.overview td,
      table.values th, table.values td {
        border-bottom: 1px solid var(--divider-color, #ccc);
        padding: 4px 8px;
        text-align: left;
        font-size: 0.9em;
      }
      table.overview th, table.overview td { text-align: center; }
      table.values td.center { text-align: center; }
      .room h3 { margin: 8px 0 4px 0; }
      hr.room-sep { border: none; border-top: 1px solid var(--divider-color, #ccc); margin: 12px 0; }
      .hl-green { color: var(--success-color, #4caf50); font-weight: bold; }
      .hl-orange { color: var(--warning-color, #ff9800); font-weight: bold; }
      .hl-red { color: var(--error-color, #f44336); font-weight: bold; }
      details summary { cursor: pointer; margin: 4px 0; }
      .empty { padding: 8px; opacity: 0.7; }
    `;
  }

  static getStubConfig() {
    return {};
  }
}

customElements.define("smart-climate-card", SmartClimateCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "smart-climate-card",
  name: "Smart Climate Karte",
  description:
    "Lüftungsübersicht für Smart Climate (JS-Variante, parallel zur Markdown-Karte nutzbar).",
});
