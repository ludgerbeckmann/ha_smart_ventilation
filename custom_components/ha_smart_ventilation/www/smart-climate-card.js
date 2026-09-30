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
 * Wird von der Integration selbst automatisch als Lovelace-Ressource
 * bereitgestellt - dadurch immer auf demselben Stand wie die installierte
 * Integration, keine eigene Versionsanzeige nötig (siehe README).
 */

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

// Erlaubt Zeilenumbrüche in langen Entity-IDs nach "." und "_" statt mitten
// im Wort (erwartet bereits escapten Text).
function breakable(escaped) {
  return escaped.replace(/([._])/g, "$1<wbr>");
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
    // Direktes Re-Rendern schon hier (nicht erst beim nächsten hass-Tick) -
    // damit eine Titel-Änderung im Editor sofort in der Vorschau sichtbar
    // wird, auch wenn hass sich zwischen zwei Ticks nicht ändert.
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 8;
  }

  static getConfigElement() {
    return document.createElement("smart-climate-card-editor");
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
      // Ein/Ausklapp-Zustand je Raum (siehe roomOpenState unten) UND je
      // "Benachrichtigungen"-Unterbereich (siehe notifyOpenState unten) -
      // "toggle" bubbelt nicht (DOM-Spezifikation), wird aber im
      // Capture-Durchlauf trotzdem an jedem Vorfahren sichtbar, deshalb
      // Listener mit useCapture=true statt der üblichen Bubble-Delegation.
      // Einmalig hier registriert (überlebt das komplette Ersetzen von
      // innerHTML bei jedem Render, da _content selbst nicht neu erzeugt
      // wird). Unterscheidung der beiden <details>-Arten über die jeweils
      // gesetzte data-Markierung.
      this._content.addEventListener(
        "toggle",
        (ev) => {
          const details = ev.target;
          if (!details || !details.dataset) return;
          if (details.dataset.room && this._roomOpenState) {
            const room = details.dataset.room;
            const entry = this._roomOpenState.get(room);
            this._roomOpenState.set(room, {
              statusClass: entry ? entry.statusClass : undefined,
              open: details.open,
            });
          } else if (details.dataset.notifyRoom && this._notifyOpenState) {
            this._notifyOpenState.set(details.dataset.notifyRoom, details.open);
          }
        },
        true
      );
      // Tippen/Klicken auf eine gekürzte Zelle klappt sie auf bzw. wieder zu
      // (auf dem Handy gibt es keinen Tooltip). Delegation auf _content, das
      // beim Rendern nicht neu erzeugt wird.
      this._content.addEventListener("click", (ev) => {
        const el = ev.target && ev.target.closest && ev.target.closest("[data-cell]");
        if (!el || !this._expandedCells) return;
        const key = el.dataset.cell;
        if (this._expandedCells.has(key)) this._expandedCells.delete(key);
        else this._expandedCells.add(key);
        el.classList.toggle("expanded", this._expandedCells.has(key));
      });
    }
    // Aufgeklappte (nicht mehr mit "..." gekürzte) Textzellen: Schlüssel
    // "<Raum>|<Zelle>". Überlebt Renders wie roomOpenState.
    if (!this._expandedCells) this._expandedCells = new Set();
    // Merkt sich je Raum den zuletzt gerenderten Status UND den aktuellen
    // Auf-/Zu-Zustand - siehe Verwendung weiter unten. Überlebt über
    // mehrere Renders hinweg (nicht Teil von innerHTML), aber nicht über
    // ein Neuladen der Seite (rein clientseitiger Zustand, bewusst nicht
    // in localStorage persistiert - siehe Zusammenfassung im Chat).
    if (!this._roomOpenState) this._roomOpenState = new Map();
    // Analog für den "Benachrichtigungen"-Unterbereich je Raum - anders als
    // roomOpenState gibt es hier keinen statusabhängigen Standardwert
    // (immer "zu" beim allerersten Rendern), daher genügt ein einfaches
    // Raum -> bool statt eines Objekts.
    if (!this._notifyOpenState) this._notifyOpenState = new Map();
    // Optionales Titel-Feld (siehe smart-climate-card-editor) - nutzt
    // ha-cards eigenes header-Attribut, damit der Titel exakt wie bei
    // Home Assistants Standard-Karten aussieht. Leer/nicht gesetzt = kein
    // Header, wie bisher.
    this._card.header = this._config.title || undefined;

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

    // Lange Texte (Grund, Auslöser, Ziele) werden nach 4 Zeilen automatisch mit
    // "…" gekürzt (CSS line-clamp, Wörter bleiben unverändert). Der volle Text
    // steht im title (Tooltip am Desktop); ein Tippen klappt die Zelle auf
    // (click-Listener oben, Zustand in _expandedCells, überlebt Neuzeichnen).
    const cellDiv = (key, html) => {
      const plain = String(html).replace(/<[^>]*>/g, "");
      return `<div class="clamp${this._expandedCells.has(key) ? " expanded" : ""}" data-cell="${esc(key)}" title="${plain}">${html}</div>`;
    };

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
        humRow = `<tr><td>Luftfeuchtigkeit</td><td class="nw">${humVal}</td><td class="nw">${outdoorHumVal} %</td><td class="nw">${Math.round(lo)} - ${Math.round(hi)} %</td></tr>`;
      }

      let co2Row = "";
      if (has(a, "co2")) {
        const co2Val = wrap(a.co2 !== null ? `${roundStr(a.co2, 0)} ppm` : "–", highlightCo2);
        const lo = Math.min(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        const hi = Math.max(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        co2Row = `<tr><td>CO2</td><td class="nw">${co2Val}</td><td class="nw">–</td><td class="nw">${Math.round(lo)} - ${Math.round(hi)} ppm</td></tr>`;
      }

      let absRow = "";
      if (has(a, "luftfeuchtigkeit")) {
        let absIn =
          has(a, "absolute_luftfeuchtigkeit") && a.absolute_luftfeuchtigkeit !== null
            ? `${a.absolute_luftfeuchtigkeit} g/m³`
            : "–";
        let absOut =
          has(a, "aussen_absolute_luftfeuchtigkeit") && a.aussen_absolute_luftfeuchtigkeit !== null
            ? `${a.aussen_absolute_luftfeuchtigkeit} g/m³`
            : "–";
        // Öffnen wegen Luftfeuchtigkeit: die absolute Luftfeuchtigkeit gibt das
        // Öffnen frei (Außenluft trockener) und wird wie der Auslöser
        // hervorgehoben - innen und außen, sofern beide Werte vorliegen.
        const absOpenGate =
          s.state === "on" && openReasons.includes("humidity") && absIn !== "–" && absOut !== "–";
        absIn = wrap(absIn, absOpenGate);
        absOut = wrap(absOut, absOpenGate || highlightCode === "outdoor_wetter");
        absRow = `<tr><td>Abs. Luftfeuchtigkeit</td><td class="nw">${absIn}</td><td class="nw">${absOut}</td><td class="nw">–</td></tr>`;
      }

      // Geräte-Tabelle
      let deviceRows = "";
      if (has(a, "luftentfeuchter_an")) {
        let name = `${a.luftentfeuchter_an ? "🔴" : "⚫"} Luftentfeuchter`;
        if (has(a, "luftentfeuchter_tank_fehler")) {
          name += `<br>${a.luftentfeuchter_tank_fehler ? "🔴" : "🟢"} Wassertank`;
        }
        let laufzeit = "–";
        if (a.luftentfeuchter_an && a.luftentfeuchter_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.luftentfeuchter_seit).getTime()) / 60000);
        } else if (has(a, "luftentfeuchter_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.luftentfeuchter_letzte_laufzeit);
        }
        const grund = has(a, "luftentfeuchter_grund") ? esc(a.luftentfeuchter_grund) : "–";
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|dehum`, grund)}</td></tr>`;
      }
      if (has(a, "klimaanlage_an")) {
        const name = `${a.klimaanlage_an ? "🔴" : "⚫"} Klimaanlage`;
        let laufzeit = "–";
        if (a.klimaanlage_an && a.klimaanlage_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.klimaanlage_seit).getTime()) / 60000);
        } else if (has(a, "klimaanlage_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.klimaanlage_letzte_laufzeit);
        }
        const grund = has(a, "klimaanlage_grund") ? esc(a.klimaanlage_grund) : "–";
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|ac`, grund)}</td></tr>`;
      }
      if (has(a, "heizung_an")) {
        let name = `${a.heizung_an ? "🔴" : "⚫"} Heizung`;
        const modeInfo = has(a, "heizung_modus") ? HEATING_MODE_LABEL[a.heizung_modus] : undefined;
        if (modeInfo) name += `<br>${modeInfo.icon} ${modeInfo.text}`;
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
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|heat`, grund)}</td></tr>`;
      }
      if (has(a, "duschen_erkannt")) {
        const name = `${a.duschen_erkannt ? "🟢" : "⚫"} Dusche`;
        let laufzeit = "–";
        if (a.duschen_erkannt && a.dusche_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.dusche_seit).getTime()) / 60000);
        } else if (has(a, "dusche_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.dusche_letzte_laufzeit);
        }
        const grund = a.duschen_erkannt ? "Luftfeuchtigkeit steigt schnell" : "–";
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|shower`, grund)}</td></tr>`;
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
          `<tr><td class="nw">${windowStateText}</td><td class="nw">–</td><td>–</td><td class="nw">${windowChangedTime}</td></tr>`;
        if (hasLiveReason) {
          empfTable += `<tr><td class="nw">–</td><td class="nw">${empfehlungText}</td><td>${cellDiv(`${a.raum}|trigger`, esc(grundLabel))}</td><td class="nw">${changedTime}</td></tr>`;
        }
        empfTable += "</tbody></table>";
      }

      const tempLo = Math.min(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const tempHi = Math.max(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const valuesTable =
        `<table class="values"><thead><tr><th>Messwert</th><th>Innen</th><th>Außen</th><th>Normalbereich</th></tr></thead><tbody>` +
        `<tr><td>Temperatur</td><td class="nw">${tempVal}</td><td class="nw">${outdoorTempVal}</td><td class="nw">${tempLo} - ${tempHi} °C</td></tr>` +
        `${humRow}${absRow}${co2Row}</tbody></table>`;

      const n1Status = has(a, "sprachausgabe_aktiv") ? "🟢" : "⚫";
      const n1Ziel = has(a, "sprachausgabe_lautsprecher") ? breakable(esc(a.sprachausgabe_lautsprecher.join(", "))) : "–";
      const n2Status = has(a, "app_aktiv") ? "🟢" : "⚫";
      const n2Ziel = has(a, "app_ziele") ? breakable(esc(a.app_ziele.join(", "))) : "–";
      const n3Status = has(a, "persistent_aktiv") ? "🟢" : "⚫";
      const notifyOpen = this._notifyOpenState.get(a.raum) || false;
      const notifyTable =
        `<details class="notify-details" data-notify-room="${esc(a.raum)}"${notifyOpen ? " open" : ""}><summary><strong>Benachrichtigungen</strong></summary>` +
        `<table class="values"><thead><tr><th>Benachrichtigung</th><th>Status</th><th>Ziel(e)</th></tr></thead><tbody>` +
        `<tr><td>Sprachausgabe</td><td class="center nw">${n1Status}</td><td>${n1Ziel === "–" ? n1Ziel : cellDiv(`${a.raum}|n1`, n1Ziel)}</td></tr>` +
        `<tr><td>App-Benachrichtigung</td><td class="center nw">${n2Status}</td><td>${n2Ziel === "–" ? n2Ziel : cellDiv(`${a.raum}|n2`, n2Ziel)}</td></tr>` +
        `<tr><td>Persistente Benachrichtigung</td><td class="center nw">${n3Status}</td><td>–</td></tr>` +
        `</tbody></table></details>`;

      const statusClass =
        matchIcon === "🔴" ? "status-red" : matchIcon === "🟠" ? "status-orange" : "status-green";

      // Standard: 🟢 eingeklappt, 🟠/🔴 aufgeklappt - manuelles Auf-/
      // Zuklappen bleibt erhalten, SOLANGE sich der Status dieses Raums
      // nicht ändert (siehe Zusammenfassung im Chat); ändert er sich,
      // wird die alte Einstellung verworfen und der Standard für den
      // neuen Status greift wieder - verhindert, dass ein Raum, der
      // gerade neu Aufmerksamkeit braucht, dauerhaft eingeklappt bleibt,
      // nur weil er vorher mal grün und manuell eingeklappt wurde.
      const defaultOpen = statusClass !== "status-green";
      const storedRoomState = this._roomOpenState.get(a.raum);
      const isOpen =
        storedRoomState && storedRoomState.statusClass === statusClass
          ? storedRoomState.open
          : defaultOpen;
      this._roomOpenState.set(a.raum, { statusClass, open: isOpen });

      const header = `<summary class="room-header"><span class="room-icon">${matchIcon}</span><h3>${esc(a.raum)}</h3></summary>`;
      let body = empfTable;
      body += valuesTable;
      if (deviceTable) body += deviceTable;
      body += notifyTable;

      const colorRank = matchIcon === "🔴" ? 0 : matchIcon === "🟠" ? 1 : 2;
      entries.push({
        sortKey: `${colorRank}${a.raum}`,
        html: `<details class="room ${statusClass}" data-room="${esc(a.raum)}"${isOpen ? " open" : ""}>${header}${body}</details>`,
      });
    }

    entries.sort((x, y) => x.sortKey.localeCompare(y.sortKey));

    const overviewCells = [
      { label: "🟢", value: String(green), cls: "ov-green" },
      { label: "🟠", value: String(orange), cls: "ov-orange" },
      { label: "🔴", value: String(red), cls: "ov-red" },
    ];
    if (summerMode !== null) {
      overviewCells.push({
        label: "Modus",
        value: summerMode ? "☀️ Sommer" : "❄️ Winter",
        cls: "",
      });
    }
    if (version !== null) {
      overviewCells.push({ label: "Integration", value: esc(version), cls: "" });
    }

    const overviewTable =
      `<table class="overview"><thead><tr>${overviewCells
        .map((c) => `<th class="${c.cls}">${c.label}</th>`)
        .join("")}</tr></thead><tbody><tr>${overviewCells
        .map((c) => `<td class="${c.cls}">${c.value}</td>`)
        .join("")}</tr></tbody></table>`;

    const roomsHtml = entries.map((e) => e.html).join("");

    this._content.innerHTML = `<div class="overview-wrap">${overviewTable}</div>${roomsHtml}`;
  }

  static _css() {
    return `
      .smart-climate-card-content { padding: 12px 6px 14px; }

      .overview-wrap { margin-bottom: 16px; }

      table.overview, table.values {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid var(--divider-color, #e0e0e0);
        margin-bottom: 10px;
      }
      table.overview th, table.overview td,
      table.values th, table.values td {
        padding: 6px 6px;
        text-align: left;
        font-size: 0.92em;
        /* Nur zwischen Wörtern umbrechen, keine Silbentrennung; ein Wort
           bricht nur im Notfall (lange Entity-IDs). Kurze Spalten (Zeiten,
           Werte, Zustände) tragen zusätzlich die Klasse .nw. */
        overflow-wrap: anywhere;
        hyphens: none;
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
        border-right: 1px solid var(--divider-color, #e0e0e0);
      }
      table.overview th:last-child, table.overview td:last-child,
      table.values th:last-child, table.values td:last-child {
        border-right: none;
      }
      table.overview tbody tr:last-child td,
      table.values tbody tr:last-child td { border-bottom: none; }
      table.overview th, table.values th {
        background: var(--secondary-background-color, rgba(127, 127, 127, 0.08));
        font-weight: 600;
        opacity: 0.85;
        white-space: nowrap;
      }
      table.overview td.nw, table.values td.nw { white-space: nowrap; }
      /* Automatische Kürzung mit "…" nach 4 Zeilen; Tippen klappt auf. */
      table.values .clamp {
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 4;
        line-clamp: 4;
        overflow: hidden;
        cursor: pointer;
      }
      table.values .clamp.expanded {
        display: block;
        -webkit-line-clamp: unset;
        line-clamp: unset;
        overflow: visible;
      }
      /* Sehr schmale Bildschirme: Nowrap lockern, damit nichts überläuft */
      @media (max-width: 340px) {
        table.overview td.nw, table.values td.nw, table.values th { white-space: normal; }
      }
      table.overview th, table.overview td { text-align: center; }
      table.overview th.ov-green, table.overview td.ov-green {
        background: rgba(76, 175, 80, 0.12);
      }
      table.overview th.ov-orange, table.overview td.ov-orange {
        background: rgba(255, 152, 0, 0.12);
      }
      table.overview th.ov-red, table.overview td.ov-red {
        background: rgba(244, 67, 54, 0.12);
      }
      table.overview td { font-size: 1.1em; font-weight: 600; }
      table.values td.center { text-align: center; }

      details.room {
        border-radius: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-left: 4px solid var(--divider-color, #e0e0e0);
        background: var(--card-background-color, transparent);
        padding: 10px 6px 12px;
        margin-bottom: 14px;
      }
      details.room:not([open]) { padding-bottom: 10px; }
      .room.status-green { border-left-color: var(--success-color, #4caf50); }
      .room.status-orange { border-left-color: var(--warning-color, #ff9800); }
      .room.status-red { border-left-color: var(--error-color, #f44336); }

      .room-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        list-style: none;
      }
      details.room[open] > .room-header { margin-bottom: 8px; }
      details.room:not([open]) > .room-header { margin-bottom: 0; }
      .room-header::-webkit-details-marker { display: none; }
      .room-header::marker { content: ""; }
      .room-header::after {
        content: "▾";
        margin-left: auto;
        opacity: 0.55;
        font-size: 0.85em;
        transition: transform 0.15s ease;
      }
      details.room:not([open]) > .room-header::after { transform: rotate(-90deg); }
      .room-icon { font-size: 1.1em; line-height: 1; }
      .room-header h3 {
        margin: 0;
        font-size: 1.15em;
        font-weight: 600;
      }

      .hl-green { color: var(--success-color, #4caf50); font-weight: bold; }
      .hl-orange { color: var(--warning-color, #ff9800); font-weight: bold; }
      .hl-red { color: var(--error-color, #f44336); font-weight: bold; }

      .notify-details {
        border-radius: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        padding: 2px 6px;
        margin-top: 4px;
      }
      .notify-details table.values { margin-top: 8px; margin-bottom: 4px; }
      .notify-details summary {
        cursor: pointer;
        padding: 6px 0;
        font-size: 0.9em;
        opacity: 0.85;
      }

      .empty { padding: 8px; opacity: 0.7; }
    `;
  }

  static getStubConfig() {
    return {};
  }
}

customElements.define("smart-climate-card", SmartClimateCard);

/*
 * Minimaler visueller Editor - ausschließlich für das optionale title-Feld.
 * Ohne diesen Editor (static getConfigElement() auf der Haupt-Karte) zeigt
 * Home Assistants Karten-Editor-Dialog generell den Hinweis "Visueller
 * Editor wird nicht unterstützt" für JEDE Custom-Card ohne eigenen Editor,
 * unabhängig von deren Config-Feldern - das Feld selbst hätte diesen
 * Hinweis also nicht verschwinden lassen, ohne diesen (bewusst schlanken)
 * Editor dazu.
 */
class SmartClimateCardEditor extends HTMLElement {
  constructor() {
    super();
    // Defensiv, falls connectedCallback (bei Einfügen ins DOM) vor
    // setConfig() feuert - die Aufrufreihenfolge ist beim Editor-Element
    // (anders als bei der Haupt-Karte, wo Lovelace setConfig() garantiert
    // vor dem Einfügen aufruft) nicht in jedem Fall dieselbe.
    this._config = {};
  }

  setConfig(config) {
    this._config = config || {};
    this._syncField();
  }

  set hass(hass) {
    this._hass = hass;
  }

  connectedCallback() {
    this._build();
  }

  _build() {
    if (this._built) return;
    this._built = true;
    // Bewusst ein natives <input> statt Home Assistants ha-textfield: Diese
    // interne Komponente wird vom Frontend nur bei Bedarf nachgeladen - wird
    // unser Editor als einer der ersten/einzigen Nutzer aufgerufen, könnte
    // sie zu dem Zeitpunkt noch nicht registriert sein, wodurch ein
    // unsichtbares, funktionsloses Element statt eines echten Eingabefelds
    // entsteht. Ein natives <input> ist dagegen immer sofort verfügbar,
    // unabhängig vom Ladezeitpunkt interner HA-Komponenten.
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <style>
        .sc-editor-field { padding: 12px 0; }
        .sc-editor-field label {
          display: block;
          font-size: 1em;
          font-weight: 700;
          margin-bottom: 6px;
        }
        .sc-editor-field input {
          width: 100%;
          box-sizing: border-box;
          padding: 8px 10px;
          font-size: 1em;
          border-radius: 4px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--card-background-color, transparent);
          color: var(--primary-text-color, inherit);
        }
      </style>
      <div class="sc-editor-field">
        <label for="sc-title-input">Titel (optional)</label>
        <input id="sc-title-input" type="text" />
      </div>
    `;
    this._field = wrapper.querySelector("input");
    this._field.addEventListener("input", (ev) => {
      const value = ev.target.value;
      const newConfig = { ...this._config };
      if (value) {
        newConfig.title = value;
      } else {
        delete newConfig.title;
      }
      this._config = newConfig;
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: newConfig },
          bubbles: true,
          composed: true,
        })
      );
    });
    this.appendChild(wrapper);
    this._syncField();
  }

  _syncField() {
    if (this._field) this._field.value = this._config.title || "";
  }
}

customElements.define("smart-climate-card-editor", SmartClimateCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "smart-climate-card",
  name: "Smart Climate Karte",
  description:
    "Lüftungsübersicht für Smart Climate (JS-Variante, parallel zur Markdown-Karte nutzbar).",
});
