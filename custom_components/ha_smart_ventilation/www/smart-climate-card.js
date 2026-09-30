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

// Geräte-Grund ohne den Vorsatz "pausiert: " (ergibt sich aus dem Status-Icon);
// der Rest beginnt mit Großbuchstaben.
function deviceReason(value) {
  const text = String(value);
  if (!text.startsWith("pausiert: ")) return esc(text);
  const rest = text.slice("pausiert: ".length);
  return esc(rest.charAt(0).toUpperCase() + rest.slice(1));
}

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
    const previous = this._config || {};
    this._config = config || {};
    // Wird die Ausklapp-Option im Editor umgeschaltet, gilt sie sofort für alle
    // Räume - der gemerkte Ein/Ausklapp-Zustand (roomOpenState) würde sonst den
    // alten Standard bis zum nächsten Statuswechsel festhalten.
    if (
      this._roomOpenState &&
      (previous.expand_attention_rooms !== false) !== (this._config.expand_attention_rooms !== false)
    ) {
      this._roomOpenState.clear();
    }
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
        const target = ev.target && ev.target.closest ? ev.target : null;
        if (!target) return;
        // Klick auf einen Wert/ein Gerät: Detailansicht (more-info) der
        // zugehörigen Entität öffnen (Standard-Ereignis von Home Assistant).
        const entityEl = target.closest("[data-entity]");
        if (entityEl) {
          this.dispatchEvent(
            new CustomEvent("hass-more-info", {
              bubbles: true,
              composed: true,
              detail: { entityId: entityEl.dataset.entity },
            })
          );
          return;
        }
        const el = target.closest("[data-cell]");
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
    // siehe README - erkennt einen Home-Assistant-Neustart, bei
    // dem mehrere Fensterkontakte gleichzeitig neu registriert wurden).
    const windowTimes = [];
    for (const id of entityIds) {
      const s = states[id];
      const a = s.attributes;
      const windowEntity = (a.entitaeten || {}).fenster;
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
    // Außenwerte sind für alle Räume gleich und stehen oben unter der
    // Statuszeile - hier der jeweils erste Raum mit einem Wert.
    const outdoor = { temp: null, hum: null, abs: null, dew: null, tempEnt: "", humEnt: "", absEnt: "", dewEnt: "" };
    let summerModeEntity = "";
    const entries = [];

    // Lange Texte (Grund, Auslöser, Ziele) werden nach 4 Zeilen automatisch mit
    // "…" gekürzt (CSS line-clamp, Wörter bleiben unverändert). Der volle Text
    // steht im title (Tooltip am Desktop); ein Tippen klappt die Zelle auf
    // (click-Listener oben, Zustand in _expandedCells, überlebt Neuzeichnen).
    const cellDiv = (key, html) => {
      const plain = String(html).replace(/<[^>]*>/g, "");
      return `<div class="clamp${this._expandedCells.has(key) ? " expanded" : ""}" data-cell="${esc(key)}" title="${plain}">${html}</div>`;
    };

    // Klickbarer Wert: öffnet per Klick die Detailansicht der Entität
    // (click-Listener oben); ohne Entity-ID bleibt der Text unverändert.
    const ent = (entityId, html) =>
      entityId ? `<span class="ent" data-entity="${esc(entityId)}">${html}</span>` : html;

    const sorted = [...entityIds].sort((idA, idB) =>
      String(states[idA].attributes.raum).localeCompare(
        String(states[idB].attributes.raum)
      )
    );

    for (const id of sorted) {
      const s = states[id];
      const a = s.attributes;

      const ents = a.entitaeten || {};
      const noWindow = has(a, "hat_fenster") && a.hat_fenster === false;
      const openReasons = a.offene_gruende || [];
      const liveGrundOpen = openReasons.length ? openReasons[0] : "";
      const liveGrundClose = a.schliessgrund_live || "";
      const highlightCode = s.state === "on" ? liveGrundOpen : liveGrundClose;
      const hasLiveReason = highlightCode !== "";

      const windowEntity = ents.fenster || "";
      let windowStateText = "–";
      let windowChangedTime = "–";
      const co2CloseException = s.state === "off" && highlightCode === "co2";
      const comfortCloseResolvedException =
        s.state === "off" &&
        ["humidity", "temp", "outdoor_warmer", "outdoor_wetter"].includes(highlightCode);
      const noWindowResolved = noWindow && comfortCloseResolvedException;

      // Fehlende Messwerte: ein konfigurierter Sensor des Raums liefert gerade
      // keinen Wert (Attribut vorhanden, aber null). Der Raum ist dann höchstens
      // grün-nach-orange angehoben; ein echter Fenster-Mismatch (rot) bleibt rot.
      const tempMissing = a.innentemperatur === undefined || a.innentemperatur === null;
      const humMissing = has(a, "luftfeuchtigkeit") && a.luftfeuchtigkeit === null;
      const co2Missing = has(a, "co2") && a.co2 === null;
      const hasMissing = tempMissing || humMissing || co2Missing;

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
      if (!summerModeEntity && ents.sommermodus) summerModeEntity = ents.sommermodus;
      if (outdoor.temp === null && has(a, "aussentemperatur") && a.aussentemperatur !== null) {
        outdoor.temp = a.aussentemperatur;
        outdoor.tempEnt = ents.aussentemperatur || "";
      }
      // Entity-IDs der konfigurierten Außensensoren auch ohne aktuellen Wert merken
      // (fehlender Wert wird in der Kachel orange markiert).
      if (!outdoor.tempEnt && ents.aussentemperatur) outdoor.tempEnt = ents.aussentemperatur;
      if (!outdoor.humEnt && ents.aussen_luftfeuchtigkeit) outdoor.humEnt = ents.aussen_luftfeuchtigkeit;
      if (outdoor.hum === null && has(a, "aussen_luftfeuchtigkeit") && a.aussen_luftfeuchtigkeit !== null) {
        outdoor.hum = a.aussen_luftfeuchtigkeit;
        outdoor.humEnt = ents.aussen_luftfeuchtigkeit || "";
      }
      if (outdoor.abs === null && has(a, "aussen_absolute_luftfeuchtigkeit") && a.aussen_absolute_luftfeuchtigkeit !== null) {
        outdoor.abs = a.aussen_absolute_luftfeuchtigkeit;
        outdoor.absEnt = ents.aussen_absolute_luftfeuchtigkeit || "";
      }
      if (outdoor.dew === null && has(a, "aussen_taupunkt") && a.aussen_taupunkt !== null) {
        outdoor.dew = a.aussen_taupunkt;
        outdoor.dewEnt = ents.aussen_taupunkt || "";
      }

      if (hasMissing && matchIcon === "🟢") matchIcon = "🟠";

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
      const missingCell = '<span class="hl-orange">–</span>';
      // Bezeichnung wie der zugehörige Wert einfärben (Hervorhebung bzw. fehlender Wert).
      const wrapLabel = (html, on, missing) =>
        on ? `<span class="${highlightClass}">${html}</span>` : missing ? `<span class="hl-orange">${html}</span>` : html;

      const tempVal = wrap(
        a.innentemperatur !== undefined && a.innentemperatur !== null
          ? `${roundStr(a.innentemperatur, 1)} °C`
          : missingCell,
        highlightTemp
      );

      let humRow = "";
      if (has(a, "luftfeuchtigkeit")) {
        const humVal = wrap(
          a.luftfeuchtigkeit !== null ? `${roundStr(a.luftfeuchtigkeit, 0)} %` : missingCell,
          highlightHum
        );
        const lo = Math.min(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
        const hi = Math.max(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
        humRow = `<tr><td>${wrapLabel(ent(ents.luftfeuchtigkeit, "Luftfeuchtigkeit"), highlightHum, a.luftfeuchtigkeit === null)}</td><td class="nw">${humVal}</td><td class="nw">${Math.round(lo)} - ${Math.round(hi)} %</td></tr>`;
      }

      let co2Row = "";
      if (has(a, "co2")) {
        const co2Val = wrap(a.co2 !== null ? `${roundStr(a.co2, 0)} ppm` : missingCell, highlightCo2);
        const lo = Math.min(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        const hi = Math.max(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
        co2Row = `<tr><td>${wrapLabel(ent(ents.co2, "CO2"), highlightCo2, a.co2 === null)}</td><td class="nw">${co2Val}</td><td class="nw">${Math.round(lo)} - ${Math.round(hi)} ppm</td></tr>`;
      }

      let absRow = "";
      if (has(a, "luftfeuchtigkeit")) {
        let absIn =
          has(a, "absolute_luftfeuchtigkeit") && a.absolute_luftfeuchtigkeit !== null
            ? `${a.absolute_luftfeuchtigkeit} g/m³`
            : "–";
        const absOutAvailable =
          has(a, "aussen_absolute_luftfeuchtigkeit") && a.aussen_absolute_luftfeuchtigkeit !== null;
        // Öffnen wegen Luftfeuchtigkeit: die absolute Luftfeuchtigkeit gibt das
        // Öffnen frei (Außenluft trockener) und wird wie der Auslöser
        // hervorgehoben - innen und außen, sofern beide Werte vorliegen.
        const absOpenGate =
          s.state === "on" && openReasons.includes("humidity") && absIn !== "–" && absOutAvailable;
        absIn = wrap(absIn, absOpenGate);
        absRow = `<tr><td>${wrapLabel(ent(ents.absolute_luftfeuchtigkeit, "Abs. Luftfeuchtigkeit"), absOpenGate, false)}</td><td class="nw">${absIn}</td><td class="nw">–</td></tr>`;
      }

      let dewRow = "";
      if (has(a, "luftfeuchtigkeit") && has(a, "taupunkt") && a.taupunkt !== null) {
        dewRow = `<tr><td>${ent(ents.taupunkt, "Taupunkt")}</td><td class="nw">${roundStr(a.taupunkt, 1)} °C</td><td class="nw">–</td></tr>`;
      }

      // Geräte-Tabelle
      let deviceRows = "";
      if (has(a, "luftentfeuchter_an")) {
        let name = ent(ents.luftentfeuchter, `${a.luftentfeuchter_an ? "🔴" : "⚫"} Luftentfeuchter`);
        if (has(a, "luftentfeuchter_tank_fehler")) {
          name += `<br>${ent(ents.luftentfeuchter_tank, `${a.luftentfeuchter_tank_fehler ? "🔴" : "🟢"} Wassertank`)}`;
        }
        let laufzeit = "–";
        if (a.luftentfeuchter_an && a.luftentfeuchter_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.luftentfeuchter_seit).getTime()) / 60000);
        } else if (has(a, "luftentfeuchter_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.luftentfeuchter_letzte_laufzeit);
        }
        const grund = has(a, "luftentfeuchter_grund") ? deviceReason(a.luftentfeuchter_grund) : "–";
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|dehum`, grund)}</td></tr>`;
      }
      if (has(a, "klimaanlage_an")) {
        const name = ent(ents.klimaanlage, `${a.klimaanlage_an ? "🔴" : "⚫"} Klimaanlage`);
        let laufzeit = "–";
        if (a.klimaanlage_an && a.klimaanlage_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.klimaanlage_seit).getTime()) / 60000);
        } else if (has(a, "klimaanlage_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.klimaanlage_letzte_laufzeit);
        }
        const grund = has(a, "klimaanlage_grund") ? deviceReason(a.klimaanlage_grund) : "–";
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|ac`, grund)}</td></tr>`;
      }
      if (has(a, "heizung_an")) {
        let name = ent(ents.heizung, `${a.heizung_an ? "🔴" : "⚫"} Heizung`);
        const modeInfo = has(a, "heizung_modus") ? HEATING_MODE_LABEL[a.heizung_modus] : undefined;
        if (modeInfo) name += `<br>${modeInfo.icon} ${modeInfo.text}`;
        let laufzeit = "–";
        if (a.heizung_an && a.heizung_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.heizung_seit).getTime()) / 60000);
        } else if (has(a, "heizung_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.heizung_letzte_laufzeit);
        }
        let grund = has(a, "heizung_grund") ? deviceReason(a.heizung_grund) : "–";
        if (has(a, "heizung_zieltemperatur") && a.heizung_zieltemperatur !== null) {
          grund += ` (Sollstellung: ${roundStr(a.heizung_zieltemperatur, 1)} °C)`;
        }
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|heat`, grund)}</td></tr>`;
      }
      if (has(a, "duschen_erkannt")) {
        const name = ent(ents.dusche, `${a.duschen_erkannt ? "🟢" : "⚫"} Dusche`);
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

      const empfehlungText = hasLiveReason ? wrap(statusText, true) : statusText;
      // Gründe ohne eigene Zeile in der Messwert-Tabelle (Frost, Hitze, Außenluft,
      // Winter-Höchstdauer) stehen weiterhin als Text unter dem Status.
      const extraReason =
        hasLiveReason && s.state !== "on" && !["temp", "humidity", "co2"].includes(highlightCode)
          ? `<br>${esc(GRUND_TEXT[highlightCode] || highlightCode)}`
          : "";

      let empfTable = "";
      if (!noWindow) {
        empfTable =
          `<table class="values"><thead><tr><th></th><th>Status</th><th>Uhrzeit</th></tr></thead><tbody>` +
          `<tr><td>${ent(windowEntity, "Fenster")}</td><td class="nw">${windowStateText}</td><td class="nw">${windowChangedTime}</td></tr>` +
          `<tr><td>${ent(id, "Empfehlung")}</td><td class="nw">${hasLiveReason ? empfehlungText + extraReason : "–"}</td><td class="nw">${hasLiveReason ? changedTime : "–"}</td></tr>` +
          "</tbody></table>";
      }

      const tempLo = Math.min(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const tempHi = Math.max(a.schwelle_temperatur_schliessen, a.schwelle_temperatur_oeffnen);
      const valuesTable =
        `<table class="values"><thead><tr><th colspan="2">Messwert</th><th>Normalbereich</th></tr></thead><tbody>` +
        `<tr><td>${wrapLabel(ent(ents.innentemperatur, "Temperatur"), highlightTemp, a.innentemperatur === undefined || a.innentemperatur === null)}</td><td class="nw">${tempVal}</td><td class="nw">${tempLo} - ${tempHi} °C</td></tr>` +
        `${humRow}${absRow}${dewRow}${co2Row}</tbody></table>`;

      const n1Status = has(a, "sprachausgabe_aktiv") ? "🟢" : "⚫";
      const n1Ziel = has(a, "sprachausgabe_lautsprecher")
        ? a.sprachausgabe_lautsprecher.map((t) => ent(t, breakable(esc(t)))).join(", ")
        : "–";
      const n2Status = has(a, "app_aktiv") ? "🟢" : "⚫";
      const n2Ziel = has(a, "app_ziele")
        ? a.app_ziele.map((t) => ent(t, breakable(esc(t)))).join(", ")
        : "–";
      const n3Status = has(a, "persistent_aktiv") ? "🟢" : "⚫";
      const notifyOpen = this._notifyOpenState.get(a.raum) || false;
      const notifyTable =
        `<details class="notify-details" data-notify-room="${esc(a.raum)}"${notifyOpen ? " open" : ""}><summary><strong>Benachrichtigungen</strong></summary>` +
        `<table class="values"><thead><tr><th>Benachrichtigung</th><th>Ziel(e)</th></tr></thead><tbody>` +
        `<tr><td><div class="nrow"><span class="ni">${n1Status}</span><span>Sprachausgabe</span></div></td><td>${n1Ziel === "–" ? n1Ziel : cellDiv(`${a.raum}|n1`, n1Ziel)}</td></tr>` +
        `<tr><td><div class="nrow"><span class="ni">${n2Status}</span><span>App-Benachrichtigung</span></div></td><td>${n2Ziel === "–" ? n2Ziel : cellDiv(`${a.raum}|n2`, n2Ziel)}</td></tr>` +
        `<tr><td><div class="nrow"><span class="ni">${n3Status}</span><span>Persistente Benachrichtigung</span></div></td><td>–</td></tr>` +
        `</tbody></table></details>`;

      const statusClass =
        matchIcon === "🔴" ? "status-red" : matchIcon === "🟠" ? "status-orange" : "status-green";

      // Standard: 🟢 eingeklappt, 🟠/🔴 aufgeklappt (abschaltbar) - manuelles Auf-/
      // Zuklappen bleibt erhalten, SOLANGE sich der Status dieses Raums
      // nicht ändert (siehe Zusammenfassung im Chat); ändert er sich,
      // wird die alte Einstellung verworfen und der Standard für den
      // neuen Status greift wieder - verhindert, dass ein Raum, der
      // gerade neu Aufmerksamkeit braucht, dauerhaft eingeklappt bleibt,
      // nur weil er vorher mal grün und manuell eingeklappt wurde.
      // Option expand_attention_rooms (Editor, Standard true): false = auch
      // 🟠/🔴 starten eingeklappt.
      const defaultOpen =
        statusClass !== "status-green" && this._config.expand_attention_rooms !== false;
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
        value: ent(summerModeEntity, summerMode ? "☀️ Sommer" : "❄️ Winter"),
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

    let outdoorTable = "";
    if (outdoor.temp !== null || outdoor.hum !== null || outdoor.abs !== null || outdoor.dew !== null || outdoor.tempEnt || outdoor.humEnt) {
      const tile = (label, valueHtml) =>
        `<div class="otile"><div class="olabel">${label}</div><div class="ovalue">${valueHtml}</div></div>`;
      outdoorTable =
        `<div class="outdoor-box"><div class="outdoor-title">Außen-Messwerte</div><div class="outdoor-tiles">` +
        tile(ent(outdoor.tempEnt, "Temperatur"), outdoor.temp !== null ? `${roundStr(outdoor.temp, 1)} °C` : outdoor.tempEnt ? '<span class="hl-orange">–</span>' : "–") +
        tile(ent(outdoor.humEnt, "Luftfeuchtigkeit"), outdoor.hum !== null ? `${roundStr(outdoor.hum, 0)} %` : outdoor.humEnt ? '<span class="hl-orange">–</span>' : "–") +
        tile(ent(outdoor.absEnt, "Abs. Luftfeuchtigkeit"), outdoor.abs !== null ? `${outdoor.abs} g/m³` : "–") +
        tile(ent(outdoor.dewEnt, "Taupunkt"), outdoor.dew !== null ? `${roundStr(outdoor.dew, 1)} °C` : "–") +
        `</div></div>`;
    }

    const roomsHtml = entries.map((e) => e.html).join("");

    this._content.innerHTML = `<div class="overview-wrap">${overviewTable}${outdoorTable}</div>${roomsHtml}`;
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
        padding: 6px 5px;
        text-align: left;
        font-size: 1em;
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
      /* Klickbare Bezeichnungen (öffnen die Detailansicht der Entität), ohne Unterstreichung. */
      .ent { cursor: pointer; }
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
      @media (max-width: 380px) {
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
      /* Außenwerte unter der Statuszeile (Bezeichnung links, Messwert rechts). */
      table.overview + table.values { margin-top: 8px; }
      table.values td.center { text-align: center; }

      details.room {
        /* Der Farbstreifen ist eine Hintergrund-Ebene (border-box): er reicht bis an den
           äußeren Rand und wird von den runden Ecken des Rahmens abgeschnitten, läuft also
           hinter den Ecken statt darüber hinaus. Die linke Rahmenlinie ist transparent,
           damit der Streifen dort sichtbar ist. */
        --stripe: var(--divider-color, #e0e0e0);
        border-radius: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-left-color: transparent;
        background:
          linear-gradient(var(--stripe), var(--stripe)) left top / 4px 100% no-repeat border-box,
          var(--card-background-color, transparent);
        padding: 10px 6px 12px 9px;
        margin-bottom: 14px;
      }
      details.room:not([open]) { padding-bottom: 10px; }
      .room.status-green { --stripe: var(--success-color, #4caf50); }
      .room.status-orange { --stripe: var(--warning-color, #ff9800); }
      .room.status-red { --stripe: var(--error-color, #f44336); }

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
      /* Methodennamen nur an Leerzeichen/Bindestrichen umbrechen, nie mitten im Wort -
         die Ziele-Spalte bricht dagegen an . und _ (siehe breakable()). */
      .notify-details table.values th:first-child,
      .notify-details table.values td:first-child { overflow-wrap: normal; word-break: normal; }
      /* Icon links, Name rechts daneben - ein Umbruch des Namens beginnt unter dem
         Namen, nicht unter dem Icon (Hängeeinzug). */
      .notify-details .nrow { display: flex; align-items: baseline; gap: 0.4em; }
      .notify-details .ni { flex: none; }
      .notify-details summary {
        cursor: pointer;
        padding: 6px 0;
        font-size: 1em;
        opacity: 0.85;
      }

      .outdoor-box { border: 1px solid var(--divider-color, #e0e0e0); border-radius: 10px; overflow: hidden; margin-bottom: 10px; container-type: inline-size; }
      .outdoor-title { padding: 6px 8px; font-weight: 600; opacity: 0.85; background: var(--secondary-background-color, rgba(127,127,127,0.08)); border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      /* Immer zwei Kacheln pro Zeile; bei breiter Karte (Container, nicht Bildschirm) vier. */
      .outdoor-tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      @container (min-width: 620px) {
        .outdoor-tiles { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      }
      .otile { padding: 6px 8px; border-right: 1px solid var(--divider-color, #e0e0e0); border-bottom: 1px solid var(--divider-color, #e0e0e0); margin: 0 -1px -1px 0; }
      .olabel { font-size: 1em; opacity: 0.85; }
      .ovalue { font-weight: 600; white-space: nowrap; }
      .empty { padding: 8px; opacity: 0.7; }
    `;
  }

  static getStubConfig() {
    return {};
  }
}

customElements.define("smart-climate-card", SmartClimateCard);

/*
 * Minimaler visueller Editor - optionales title-Feld und die Option
 * expand_attention_rooms (Räume mit Handlungsbedarf aufgeklappt).
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
        .sc-editor-check { padding: 4px 0 12px; }
        .sc-editor-check label { display: flex; gap: 8px; align-items: center; cursor: pointer; }
        .sc-editor-check input { width: auto; margin: 0; }
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
      <div class="sc-editor-check">
        <label>
          <input id="sc-expand-input" type="checkbox" />
          Räume mit Handlungsbedarf (🟠/🔴) aufgeklappt anzeigen
        </label>
      </div>
    `;
    this._field = wrapper.querySelector("#sc-title-input");
    this._expand = wrapper.querySelector("#sc-expand-input");
    const emit = (newConfig) => {
      this._config = newConfig;
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: newConfig },
          bubbles: true,
          composed: true,
        })
      );
    };
    this._field.addEventListener("input", (ev) => {
      const value = ev.target.value;
      const newConfig = { ...this._config };
      if (value) {
        newConfig.title = value;
      } else {
        delete newConfig.title;
      }
      emit(newConfig);
    });
    this._expand.addEventListener("change", (ev) => {
      const newConfig = { ...this._config };
      // Standard ist "aufgeklappt" - nur die Abweichung wird gespeichert.
      if (ev.target.checked) {
        delete newConfig.expand_attention_rooms;
      } else {
        newConfig.expand_attention_rooms = false;
      }
      emit(newConfig);
    });
    this.appendChild(wrapper);
    this._syncField();
  }

  _syncField() {
    if (this._field) this._field.value = this._config.title || "";
    if (this._expand) this._expand.checked = this._config.expand_attention_rooms !== false;
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
