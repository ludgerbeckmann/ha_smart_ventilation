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
  no_need: "Kein Lüftungsbedarf",
};

// Raumstatus (Attribut `raumstatus`) -> Ampel-Symbol.
const ROOM_STATUS_ICONS = {
  ok: "🟢",
  hinweis: "🟠",
  handlungsbedarf: "🔴",
};

const HEATING_MODE_LABEL = {
  comfort: { icon: "🔴", text: "Komfort" },
  night: { icon: "🟡", text: "Eco (Nacht)" },
  building_protection: { icon: "🔵", text: "Gebäudeschutz" },
  standby: { icon: "🟠", text: "Standby" },
};

// Jeder Text in Klammern (z. B. "(Sollstellung: 17.0 °C)") steht in einer
// eigenen Zeile; das Leerzeichen davor bleibt für Tooltip/Textkopie erhalten.
function parenBreak(html) {
  return String(html).replace(/\s*\(/g, " <br>(");
}

// Geräte-Grund ohne den Vorsatz "pausiert: " (ergibt sich aus dem Status-Icon);
// der Rest beginnt mit Großbuchstaben. Klammern stehen in eigener Zeile.
function deviceReason(value) {
  const text = String(value);
  if (!text.startsWith("pausiert: ")) return parenBreak(esc(text));
  const rest = text.slice("pausiert: ".length);
  return parenBreak(esc(rest.charAt(0).toUpperCase() + rest.slice(1)));
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

// Sollwert im Home-Assistant-Stil: ganze Zahl groß, Nachkommastelle und Einheit klein.
function scSetpointHtml(value) {
  const t = roundStr(value, 1);
  if (t === null) return "";
  const [whole, dec] = t.split(".");
  return `<span class="sc-th-num">${esc(whole)}</span><span class="sc-th-side"><small class="sc-th-unit">°C</small><small class="sc-th-dec">,${esc(dec || "0")}</small></span>`;
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

// Infos zum gewollten Heizungs-Modus für Tabelle und Raum-Dialog:
// "Soll Standby seit 22:14 (vor 3h 20 Min)", ein verhinderter Comfort und
// eine manuelle Übersteuerung. Alles bereits escaped; fehlende Attribute
// (ältere Integration) ergeben leere Teile.
function heatingInfo(a, todayStr) {
  const out = { since: "", prevented: "", override: "", learned: "" };
  const wanted = has(a, "heizung_soll_modus") ? HEATING_MODE_LABEL[a.heizung_soll_modus] : undefined;
  if (wanted && has(a, "heizung_modus_seit") && a.heizung_modus_seit) {
    const d = new Date(a.heizung_modus_seit);
    if (!Number.isNaN(d.getTime())) {
      out.since = `Soll ${esc(wanted.text)} seit ${esc(shortTimeStr(d, todayStr))} (vor ${esc(fmtDuration((Date.now() - d.getTime()) / 60000))})`;
    }
  } else if (wanted) {
    out.since = `Soll ${esc(wanted.text)}`;
  }
  if (a.heizung_verhindert === "anwesenheit") out.prevented = "Comfort verhindert: niemand zuhause";
  else if (a.heizung_verhindert === "ferien") out.prevented = "Comfort verhindert: Ferien-/Werktagssensor";
  if (a.heizung_uebersteuert && a.heizung_uebersteuerung_seit) {
    const d = new Date(a.heizung_uebersteuerung_seit);
    if (!Number.isNaN(d.getTime())) out.override = `Manuell übersteuert seit ${esc(shortTimeStr(d, todayStr))}`;
  }
  if (has(a, "nutzung_lerntage")) {
    const wd = has(a, "nutzung_gelernt_werktag") ? a.nutzung_gelernt_werktag : "";
    const we = has(a, "nutzung_gelernt_wochenende") ? a.nutzung_gelernt_wochenende : "";
    if (wd || we) {
      const bits = [];
      if (wd) bits.push(`Werktag ${wd}`);
      if (we) bits.push(`Wochenende ${we}`);
      out.learned = `Gelernte Nutzung: ${esc(bits.join(", "))}${a.nutzung_aktiv ? "" : " (nur Anzeige)"}`;
    } else {
      out.learned = `Nutzung wird gelernt (${esc(String(a.nutzung_lerntage))} Tage)`;
    }
  }
  return out;
}

function has(attrs, key) {
  return Object.prototype.hasOwnProperty.call(attrs, key);
}

// ---------------------------------------------------------------------------
// Kompakte Raumansicht für den Raum-Dialog (compact_room): Home-Assistant-Stil
// mit Abschnitten, Zeilen (Symbol, Name, Zweitzeile, Wert) und Balken für den
// Normalbereich statt Tabellen. Nutzt dieselben, in _render() berechneten Werte.
// ---------------------------------------------------------------------------
const SC_COLOR = {
  green: "var(--success-color, #4caf50)",
  orange: "var(--warning-color, #ff9800)",
  red: "var(--error-color, #f44336)",
  blue: "var(--info-color, #2196f3)",
  grey: "var(--secondary-text-color, #727272)",
};
const SC_HL_COLOR = { "hl-green": SC_COLOR.green, "hl-orange": SC_COLOR.orange, "hl-red": SC_COLOR.red };
const SC_STATUS_LABEL = { ok: "OK", hinweis: "Hinweis", handlungsbedarf: "Handlungsbedarf" };
const SC_STATUS_COLOR = { ok: SC_COLOR.green, hinweis: SC_COLOR.orange, handlungsbedarf: SC_COLOR.red };
// Farben wie beim Ventil-Balken der Bubble-Card (Modul climate_status).
const SC_HEATING_COLOR = {
  comfort: "var(--state-climate-heat-color, rgb(255, 99, 71))",
  standby: "var(--warning-color, rgb(255, 193, 7))",
  night: "var(--state-climate-auto-color, rgb(102, 187, 106))",
  building_protection: "var(--state-climate-cool-color, rgb(75, 177, 254))",
};
// Preset-Name des Geräts (herstellerabhängig) -> Modus für die Farbe.
function scPresetMode(name) {
  const n = String(name || "").toLowerCase();
  if (/comfort|komfort/.test(n)) return "comfort";
  if (/standby|home/.test(n)) return "standby";
  if (/eco|night|nacht|sleep/.test(n)) return "night";
  if (/protect|schutz|away/.test(n)) return "building_protection";
  return "";
}

// Heizplan des Tages (Attribut heizung_tagesplan = [[Startminute, Modus], ...]):
// Farbbalken über 0-24 Uhr mit "jetzt"-Markierung, Skala und den Wechselzeiten.
// Modus "" = für diesen Abschnitt gibt es keinen Plan (schraffiert).
const SC_PLAN_COLOR = {
  comfort: SC_HEATING_COLOR.comfort,
  standby: SC_HEATING_COLOR.standby,
  night: SC_HEATING_COLOR.night,
  building_protection: SC_HEATING_COLOR.building_protection,
};
const PLAN_LABEL = {
  comfort: "Komfort",
  standby: "Standby",
  night: "Eco (Nacht)",
  building_protection: "Gebäudeschutz",
};

// Liste [[Startminute, Modus], ...] bereinigen und sortieren.
function planEntries(list) {
  const out = [];
  if (!Array.isArray(list)) return out;
  for (const entry of list) {
    if (!Array.isArray(entry)) continue;
    const start = Number(entry[0]);
    if (!Number.isFinite(start) || start < 0 || start >= 1440) continue;
    out.push([start, typeof entry[1] === "string" ? entry[1] : ""]);
  }
  out.sort((x, y) => x[0] - y[0]);
  return out;
}

// Modus einer sortierten Liste zur Minute t ("" = noch kein Eintrag).
function planModeAt(entries, t) {
  let mode = "";
  for (const [start, m] of entries) {
    if (start <= t) mode = m;
    else break;
  }
  return mode;
}

// history (Attribut heizung_tagesverlauf): was bis jetzt wirklich lief. Bis zur
// Jetzt-Marke gilt der echte Verlauf (volle Farbe), danach der Plan (abgedunkelt);
// wo kein Verlauf bekannt ist, bleibt der Plan stehen.
function planHtml(plan, now, compact, history) {
  const planE = planEntries(plan);
  const histE = planEntries(history).filter((e) => e[1] !== "");
  if (!planE.length && !histE.length) return "";
  const d = now instanceof Date ? now : new Date();
  const nowMin = d.getHours() * 60 + d.getMinutes();
  const hasHist = histE.length > 0;
  const cuts = new Set([0, ...planE.map((e) => e[0]), ...planEntries(history).map((e) => e[0])]);
  if (hasHist && nowMin > 0 && nowMin < 1440) cuts.add(nowMin);
  const points = [...cuts].sort((x, y) => x - y);
  const segs = [];
  points.forEach((start, i) => {
    const end = i + 1 < points.length ? points[i + 1] : 1440;
    const past = hasHist && start < nowMin;
    let mode = past ? planModeAt(planEntries(history), start) : "";
    if (!mode) mode = planModeAt(planE, start);
    const fut = hasHist && !past;
    const last = segs[segs.length - 1];
    if (last && last.mode === mode && last.fut === fut) last.end = end;
    else segs.push({ start, end, mode, fut });
  });
  const hhmm = (m) => `${pad2(Math.floor(m / 60))}:${pad2(m % 60)}`;
  let bar = "";
  const times = [];
  let lastMode = null;
  for (const s of segs) {
    const known = Object.prototype.hasOwnProperty.call(SC_PLAN_COLOR, s.mode);
    const label = known ? PLAN_LABEL[s.mode] : "kein Plan";
    bar += `<span class="plan-seg${known ? "" : " plan-none"}${s.fut ? " plan-fut" : ""}" style="flex:${s.end - s.start} 0 0;${known ? `background:${SC_PLAN_COLOR[s.mode]}` : ""}" title="${hhmm(s.start)}–${s.end >= 1440 ? "24:00" : hhmm(s.end)} ${esc(label)}"></span>`;
    if (known && s.mode !== lastMode) {
      times.push(`<span class="plan-t"><span class="plan-dot" style="background:${SC_PLAN_COLOR[s.mode]}"></span>${hhmm(s.start)} ${esc(label)}</span>`);
    }
    lastMode = s.mode;
  }
  const nowPct = (nowMin / 1440) * 100;
  const tick = (h) =>
    `<span style="${h === 0 ? "left:0;transform:none" : h === 24 ? "right:0;transform:none" : `left:${(h / 24) * 100}%`}">${h}</span>`;
  return (
    `<div class="plan"><div class="plan-wrap"><div class="plan-bar">${bar}</div>` +
    `<div class="plan-now" style="left:${nowPct.toFixed(2)}%"></div></div>` +
    `<div class="plan-scale">${[0, 6, 12, 18, 24].map(tick).join("")}</div>` +
    (compact ? "" : `<div class="plan-times">${times.join("")}</div>`) +
    "</div>"
  );
}

// Geräte-Grund als reiner Text (ohne Zeilenumbrüche), ohne Vorsatz "pausiert: ".
function plainReason(value) {
  const text = String(value);
  const rest = text.startsWith("pausiert: ") ? text.slice("pausiert: ".length) : text;
  return esc(rest.charAt(0).toUpperCase() + rest.slice(1));
}

function crFmt(n) {
  const num = Number(n);
  return Number.isInteger(num) ? String(num) : num.toFixed(1);
}

function crCompactRoom(c) {
  const { a, ents, ent, expandedCells } = c;
  const icon = (name, color) =>
    `<div class="cr-ico" style="--c:${color}"><ha-icon icon="${name}"></ha-icon></div>`;
  const named = (entityId, html) => (entityId ? ent(entityId, html) : html);
  const clamp = (key, html) =>
    `<div class="cr-s cr-clamp${expandedCells.has(key) ? " expanded" : ""}" data-cell="${esc(key)}" title="${String(html).replace(/<[^>]*>/g, "")}">${html}</div>`;

  const row = (o) => {
    const sub = o.sub
      ? o.clampKey
        ? clamp(o.clampKey, o.sub)
        : `<div class="cr-s">${o.sub}</div>`
      : "";
    let right = "";
    if (o.chip) right = `<span class="cr-chip" style="--c:${o.chipColor}">${o.chip}</span>`;
    else if (o.right) right = `<span class="cr-v"${o.rightColor ? ` style="color:${o.rightColor}"` : ""}>${o.right}</span>`;
    return `<div class="cr-row${o.entityId ? " cr-link" : ""}"${o.entityId ? ` data-rowent="${esc(o.entityId)}"` : ""}>${icon(o.icon, o.color)}<div class="cr-t"><div class="cr-p">${named(o.entityId, o.title)}${o.titleExtra ? ` <span class="cr-s">${o.titleExtra}</span>` : ""}</div>${sub}</div>${right}</div>`;
  };

  // Zeile mit Normalbereich-Balken: Bereich grün hinterlegt, Punkt = aktueller Wert.
  const gauge = (o) => {
    const v = o.value === null || o.value === undefined ? NaN : Number(o.value);
    const rangeOk = Number.isFinite(o.lo) && Number.isFinite(o.hi);
    const span = Math.max(o.hi - o.lo, 0.0001);
    let bar = "";
    let color = o.color;
    if (!Number.isNaN(v) && rangeOk) {
      const min = Math.min(o.lo - span * 0.8, v - span * 0.2);
      const max = Math.max(o.hi + span * 0.8, v + span * 0.2);
      const pos = (x) => Math.max(2, Math.min(98, ((x - min) / (max - min)) * 100));
      bar = `<div class="cr-bar"><div class="cr-band" style="left:${pos(o.lo)}%;width:${pos(o.hi) - pos(o.lo)}%"></div><div class="cr-mk" style="left:${pos(v)}%;--c:${color}"></div></div>`;
    } else if (Number.isNaN(v)) {
      color = SC_COLOR.orange;
    }
    const rangeText = rangeOk ? `<span class="cr-s">${crFmt(o.lo)} – ${crFmt(o.hi)} ${o.unit}</span>` : "";
    const valueHtml = Number.isNaN(v) ? "–" : esc(o.valueText);
    return `<div class="cr-row${o.entityId ? " cr-link" : ""}"${o.entityId ? ` data-rowent="${esc(o.entityId)}"` : ""}>${icon(o.icon, color)}<div class="cr-t"><div class="cr-gl"><span class="cr-p">${named(o.entityId, o.label)}</span>${rangeText}</div>${bar}${o.extra ? `<div class="cr-s cr-xtra">${o.extra}</div>` : ""}</div><span class="cr-v cr-gv${o.big ? " cr-big" : ""}" style="color:${color}">${valueHtml}</span></div>`;
  };

  const hlColor = SC_HL_COLOR[c.highlightClass] || SC_COLOR.orange;
  const status = c.status;
  const SC_STATUS_ICON = { ok: "mdi:check-circle-outline", hinweis: "mdi:alert-circle-outline", handlungsbedarf: "mdi:alert-outline" };
  const headerInfo = { name: a.raum, label: SC_STATUS_LABEL[status] || "OK", color: SC_STATUS_COLOR[status] || SC_COLOR.green, icon: SC_STATUS_ICON[status] || SC_STATUS_ICON.ok };
  let html = "";
  if (c.headerOut) {
    // Der Raum-Dialog zeigt Name und Status selbst in seiner Kopfzeile.
    Object.assign(c.headerOut, headerInfo);
  } else {
    html = `<div class="cr-top"><h1>${esc(a.raum)}</h1><span class="cr-hchip" style="--c:${headerInfo.color}"><i></i>${headerInfo.label}</span></div>`;
  }

  // --- Lüften ---------------------------------------------------------------
  let vent = "";
  if (!c.noWindow) {
    const w = c.windowState;
    const open = w === "on";
    const known = w === "on" || w === "off";
    vent += row({
      icon: open ? "mdi:window-open-variant" : "mdi:window-closed-variant",
      color: open ? SC_COLOR.blue : SC_COLOR.grey,
      title: "Fenster",
      entityId: c.windowEntity,
      sub: known ? `${open ? "geöffnet" : "geschlossen"}${c.windowChangedTime !== "–" ? ` seit ${esc(c.windowChangedTime)}` : ""}` : "unbekannt",
      right: known ? (open ? "Geöffnet" : "Geschlossen") : "–",
    });
    vent += row({
      icon: "mdi:bell-outline",
      color: c.hasLiveReason ? hlColor : SC_COLOR.grey,
      title: "Empfehlung",
      entityId: c.id,
      titleExtra: c.hasLiveReason && c.changedTime !== "–" ? `seit ${esc(c.changedTime)}` : "",
      sub: c.hasLiveReason ? c.reasonText : "Aktuell keine Empfehlung",
      clampKey: c.hasLiveReason ? `${a.raum}|reason` : "",
      chip: c.hasLiveReason ? esc(c.statusText) : "",
      chipColor: hlColor,
    });
  }
  const ventSection = vent ? `<div class="cr-sec">${vent}</div>` : "";

  // --- Messwerte ------------------------------------------------------------
  let vals = "";
  const tempVal = a.innentemperatur === undefined ? null : a.innentemperatur;
  // Farbe nach Normalbereich (nicht nach Empfehlung): unter dem Bereich
  // `below`, darüber `above`, im Bereich grün; ohne Grenzen neutral.
  const colorFor = (v, lo, hi, below, above) => {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return SC_COLOR.grey;
    if (!Number.isFinite(lo) || !Number.isFinite(hi)) return SC_COLOR.grey;
    if (Number(v) < lo) return below;
    if (Number(v) > hi) return above;
    return SC_COLOR.green;
  };
  // Abgeleitete Werte stehen als kleine Zeile unter dem Balken der Größe, zu der sie gehören.
  const dewExtra = has(a, "luftfeuchtigkeit") && has(a, "taupunkt") && a.taupunkt !== null
    ? `<span>${named(ents.taupunkt, "Taupunkt")}</span><span class="nw">${roundStr(a.taupunkt, 1)}&nbsp;°C</span>` : "";
  let absExtra = "";
  if (has(a, "luftfeuchtigkeit")) {
    const absText = has(a, "absolute_luftfeuchtigkeit") && a.absolute_luftfeuchtigkeit !== null ? `${a.absolute_luftfeuchtigkeit}&nbsp;g/m³` : "–";
    absExtra = `<span>${named(ents.absolute_luftfeuchtigkeit, "Abs. Luftfeuchtigkeit")}</span><span class="nw"${c.absOpenGate ? ` style="color:${hlColor}"` : ""}>${absText}</span>`;
  }
  vals += gauge({
    icon: "mdi:thermometer", label: "Temperatur", entityId: ents.innentemperatur,
    value: tempVal, valueText: `${roundStr(tempVal, 1)} °C`, lo: c.tempLo, hi: c.tempHi, unit: "°C", big: true, extra: dewExtra,
    color: colorFor(tempVal, c.tempLo, c.tempHi, SC_COLOR.blue, SC_COLOR.red),
  });
  if (has(a, "luftfeuchtigkeit")) {
    const lo = Math.min(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
    const hi = Math.max(a.schwelle_feuchtigkeit_schliessen, a.schwelle_feuchtigkeit_oeffnen);
    vals += gauge({
      icon: "mdi:water-percent", label: "Luftfeuchtigkeit", entityId: ents.luftfeuchtigkeit,
      value: a.luftfeuchtigkeit, valueText: `${roundStr(a.luftfeuchtigkeit, 0)} %`, lo, hi, unit: "%", big: true, extra: absExtra,
      color: colorFor(a.luftfeuchtigkeit, lo, hi, SC_COLOR.orange, SC_COLOR.blue),
    });
  }
  if (has(a, "co2")) {
    const lo = Math.min(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
    const hi = Math.max(a.schwelle_co2_schliessen, a.schwelle_co2_oeffnen);
    vals += gauge({
      icon: "mdi:molecule-co2", label: "CO2", entityId: ents.co2,
      value: a.co2, valueText: `${roundStr(a.co2, 0)} ppm`, lo, hi, unit: "ppm",
      color: colorFor(a.co2, lo, hi, SC_COLOR.green, SC_COLOR.red),
    });
  }
  // Heizungssteuerung des Dialogs: Platzhalter, in den die Karte nach jedem
  // Neuzeichnen das dauerhafte Thermostat-Element wieder einsetzt.
  const thermoSlot = c.thermo ? `<div class="cr-thermo-slot"></div>` : "";
  // Heizplan: direkt unter dem Sollwert, in derselben Karte.
  let planRow = "";
  if (has(a, "heizung_an") && ((has(a, "heizung_tagesplan") && Array.isArray(a.heizung_tagesplan)) || (has(a, "heizung_tagesverlauf") && Array.isArray(a.heizung_tagesverlauf)))) {
    const planBlock = planHtml(a.heizung_tagesplan, undefined, false, a.heizung_tagesverlauf);
    if (planBlock) {
      const planOpen = c.planOpen === true;
      planRow = `<div class="cr-row cr-plan"><div class="cr-t"><div class="cr-planfold${planOpen ? " open" : ""}" data-plan-room="${esc(a.raum)}">` +
        `<div class="cr-plansum" data-plan-toggle role="button" tabindex="0" aria-expanded="${planOpen}"><span class="cr-p">Heizplan</span><ha-icon class="cr-chev" icon="mdi:chevron-right"></ha-icon></div>${planBlock}</div></div></div>`;
    }
  }
  html += `<div class="cr-sec">${vals}${thermoSlot}${planRow}</div>` + ventSection;

  // --- Geräte ---------------------------------------------------------------
  const runtime = (on, since, last) => {
    if (on && since) return fmtDuration((Date.now() - new Date(since).getTime()) / 60000);
    if (last !== undefined && last !== null) return fmtDuration(last);
    return "–";
  };
  // Kachelreihe: Symbol, Minuten und kurze Bezeichnung; der Text steht unter der
  // Reihe und klappt per Tipp auf die Kachel auf (immer nur ein Gerät).
  const devs = [];
  const addDev = (d) => devs.push(d);
  if (has(a, "luftentfeuchter_an")) {
    const parts = [a.luftentfeuchter_an ? "Läuft" : "Aus"];
    if (has(a, "luftentfeuchter_grund") && a.luftentfeuchter_grund) parts.push(plainReason(a.luftentfeuchter_grund));
    const tank = has(a, "luftentfeuchter_tank_fehler") && a.luftentfeuchter_tank_fehler;
    if (tank) parts.push(`<span style="color:${SC_COLOR.red}">Tank voll</span>`);
    addDev({
      key: "dehum", icon: "mdi:air-humidifier", color: tank ? SC_COLOR.red : a.luftentfeuchter_an ? SC_COLOR.blue : SC_COLOR.grey,
      name: "Entfeuchter", title: "Luftentfeuchter", entityId: ents.luftentfeuchter, text: parts.join(" · "),
      minutes: runtime(a.luftentfeuchter_an, a.luftentfeuchter_seit, a.luftentfeuchter_letzte_laufzeit),
    });
  }
  if (has(a, "klimaanlage_an")) {
    const parts = [a.klimaanlage_an ? "Läuft" : "Aus"];
    if (has(a, "klimaanlage_grund") && a.klimaanlage_grund) parts.push(plainReason(a.klimaanlage_grund));
    addDev({
      key: "ac", icon: "mdi:air-conditioner", color: a.klimaanlage_an ? SC_COLOR.blue : SC_COLOR.grey,
      name: "Klima", title: "Klimaanlage", entityId: ents.klimaanlage, text: parts.join(" · "),
      minutes: runtime(a.klimaanlage_an, a.klimaanlage_seit, a.klimaanlage_letzte_laufzeit),
    });
  }
  if (has(a, "heizung_an")) {
    const mode = has(a, "heizung_modus") ? HEATING_MODE_LABEL[a.heizung_modus] : undefined;
    const parts = [];
    if (mode) parts.push(esc(mode.text));
    const hi = heatingInfo(a, c.todayStr);
    if (hi.since) parts.push(hi.since);
    if (has(a, "heizung_grund") && a.heizung_grund) parts.push(plainReason(a.heizung_grund));
    if (hi.prevented) parts.push(hi.prevented);
    if (hi.override) parts.push(hi.override);
    if (hi.learned) parts.push(hi.learned);
    if (has(a, "heizung_zieltemperatur") && a.heizung_zieltemperatur !== null) {
      parts.push(`Sollstellung ${roundStr(a.heizung_zieltemperatur, 1)} °C`);
    }
    addDev({
      key: "heat", icon: "mdi:radiator", color: SC_HEATING_COLOR[a.heizung_modus] || (a.heizung_an ? SC_COLOR.orange : SC_COLOR.grey),
      name: "Heizung", title: "Heizung", entityId: ents.heizung, text: parts.join(" · "),
      minutes: runtime(a.heizung_an, a.heizung_seit, a.heizung_letzte_laufzeit),
    });
  }
  if (has(a, "duschen_erkannt")) {
    let sub = a.duschen_erkannt ? "Luftfeuchtigkeit steigt schnell" : "";
    if (has(a, "dusche_letzter_start") && a.dusche_letzter_start) {
      const t = `Start ${shortTimeStr(new Date(a.dusche_letzter_start), c.todayStr)}`;
      sub = a.duschen_erkannt ? `${sub} · ${t}` : `Letzter ${t}`;
    }
    addDev({
      key: "shower", icon: "mdi:shower-head", color: a.duschen_erkannt ? SC_COLOR.blue : SC_COLOR.grey,
      name: "Dusche", title: "Dusche", entityId: ents.dusche, text: sub,
      minutes: runtime(a.duschen_erkannt, a.dusche_seit, a.dusche_letzte_laufzeit),
    });
  }
  if (devs.length) {
    const openKey = c.devOpen && devs.some((d) => d.key === c.devOpen) ? c.devOpen : "";
    const tiles = devs.map((d) =>
      `<button type="button" class="cr-dev${openKey === d.key ? " open" : ""}" data-dev="${d.key}" aria-expanded="${openKey === d.key}" style="--c:${d.color}">` +
      `<span class="cr-ico"><ha-icon icon="${d.icon}"></ha-icon></span><span class="cr-dv">${esc(d.minutes)}</span><span class="cr-dn">${esc(d.name)}</span></button>`
    ).join("");
    const details = devs.map((d) =>
      `<div class="cr-devdetail${openKey === d.key ? " open" : ""}" data-devd="${d.key}"${d.entityId ? ` data-rowent="${esc(d.entityId)}"` : ""}>` +
      `<span class="cr-p">${esc(d.title)}</span>${d.text ? `<div class="cr-s">${d.text}</div>` : ""}</div>`
    ).join("");
    html += `<div class="cr-sec cr-devsec"><div class="cr-devs" data-dev-room="${esc(a.raum)}">${tiles}</div>${details}</div>`;
  }

  // --- Benachrichtigungen (aufklappbar, Zustand je Raum) ---------------------
  const targets = (list) =>
    list && list.length ? list.map((t) => ent(t, breakable(esc(t)))).join("<br>") : "";
  const nrow = (iconName, title, activeKey, list) => {
    const on = has(a, activeKey);
    return row({
      icon: iconName, color: on ? SC_COLOR.green : SC_COLOR.grey, title,
      sub: targets(list), right: on ? "Aktiv" : "Aus", rightColor: on ? SC_COLOR.green : SC_COLOR.grey,
    });
  };
  const notifyRows =
    nrow("mdi:speaker", "Sprachausgabe", "sprachausgabe_aktiv", a.sprachausgabe_lautsprecher) +
    nrow("mdi:cellphone", "Push-Benachrichtigung", "app_aktiv", a.app_ziele) +
    nrow("mdi:message-text-outline", "Persistente Benachrichtigung", "persistent_aktiv", null);
  if (c.notifyOut) {
    // Raum-Dialog: Die Methoden stehen im Menü der Glocke in der Kopfzeile.
    c.notifyOut.html = notifyRows;
  } else {
    html +=
      `<div class="cr-sec"><details class="cr-notify" data-notify-room="${esc(a.raum)}"${c.notifyOpen ? " open" : ""}>` +
      `<summary class="cr-fold">${icon("mdi:bell-outline", SC_COLOR.grey)}<span class="cr-ft">Methoden und Ziele</span><ha-icon class="cr-chev" icon="mdi:chevron-right"></ha-icon></summary>` +
      notifyRows +
      `</details></div>`;
  }
  return html;
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
        // Heizplan: Pfeil klappt die Wechselzeiten auf/zu (Zustand je Raum).
        const planSum = target.closest("[data-plan-toggle]");
        if (planSum && this._planOpen) {
          const fold = planSum.closest(".cr-planfold");
          if (fold) {
            const open = !fold.classList.contains("open");
            fold.classList.toggle("open", open);
            planSum.setAttribute("aria-expanded", String(open));
            const room = fold.dataset.planRoom;
            if (open) this._planOpen.add(room);
            else this._planOpen.delete(room);
          }
          return;
        }
        // Geräte-Kachel: Text darunter auf-/zuklappen (immer nur ein Gerät je Raum).
        const tile = target.closest("[data-dev]");
        if (tile && this._devOpen) {
          const wrap = tile.closest("[data-dev-room]");
          const room = wrap ? wrap.dataset.devRoom : "";
          const key = tile.dataset.dev;
          const open = this._devOpen.get(room) !== key;
          if (open) this._devOpen.set(room, key);
          else this._devOpen.delete(room);
          const sec = tile.closest(".cr-devsec");
          if (sec) {
            sec.querySelectorAll("[data-dev]").forEach((t) => {
              const on = open && t.dataset.dev === key;
              t.classList.toggle("open", on);
              t.setAttribute("aria-expanded", String(on));
            });
            sec.querySelectorAll("[data-devd]").forEach((d) => d.classList.toggle("open", open && d.dataset.devd === key));
          }
          return;
        }
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
        if (!el) {
          // Tipp irgendwo in einer Zeile: more-info der Zeilen-Entität.
          const rowEl = target.closest("[data-rowent]");
          if (rowEl) {
            this.dispatchEvent(
              new CustomEvent("hass-more-info", {
                bubbles: true,
                composed: true,
                detail: { entityId: rowEl.dataset.rowent },
              })
            );
          }
          return;
        }
        if (!this._expandedCells) return;
        const key = el.dataset.cell;
        if (this._expandedCells.has(key)) this._expandedCells.delete(key);
        else this._expandedCells.add(key);
        el.classList.toggle("expanded", this._expandedCells.has(key));
      });
    }
    // Aufgeklappte (nicht mehr mit "..." gekürzte) Textzellen: Schlüssel
    // "<Raum>|<Zelle>". Überlebt Renders wie roomOpenState.
    if (!this._expandedCells) this._expandedCells = new Set();
    // Räume, deren Heizplan-Legende (Wechselzeiten) im Raum-Dialog aufgeklappt ist.
    if (!this._planOpen) this._planOpen = new Set();
    // Aufgeklapptes Gerät der Kachelreihe je Raum (Raum -> Schlüssel).
    if (!this._devOpen) this._devOpen = new Map();
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
    this._card.classList.toggle("sc-compact", this._config.compact_room === true);

    if (!entityIds.length) {
      this._content.innerHTML =
        '<div class="empty">Keine Räume gefunden (kein binary_sensor mit "raum"-Attribut).</div>';
      return;
    }

    // Pass 1: Fenster-Zeitstempel sammeln (für den "Massen-Reset"-Filter,
    // siehe README - erkennt einen Home-Assistant-Neustart, bei
    // dem mehrere Fensterkontakte gleichzeitig neu registriert wurden).
    // Nur für Räume ohne Attribut fenster_seit (dort liefert die Integration
    // den echten Zeitpunkt aus der Verlaufsdatenbank, kein Filter nötig).
    const windowTimes = [];
    for (const id of entityIds) {
      const s = states[id];
      const a = s.attributes;
      const windowEntity = (a.entitaeten || {}).fenster;
      if (windowEntity && states[windowEntity] && !a.fenster_seit) {
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
    const headerOut = {};
    const notifyOut = this._notifyMenu ? {} : null;

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

      // Ampel des Raums: kommt fertig berechnet vom Backend (Attribut
      // `raumstatus`, siehe CLAUDE.md Lektion 103) - dieselbe Quelle wie der
      // Sensor "‹Raum› Raumstatus".
      const matchIcon = ROOM_STATUS_ICONS[a.raumstatus] || "🟢";
      let highlightOk = false;

      if (windowEntity && states[windowEntity]) {
        const w = states[windowEntity].state;
        windowStateText = w === "on" ? "geöffnet" : w === "off" ? "geschlossen" : "unbekannt";
        if (w === "on" || w === "off") {
          if (a.fenster_seit) {
            windowChangedTime = shortTimeStr(new Date(a.fenster_seit), todayStr);
          } else {
            const windowDt = new Date(states[windowEntity].last_changed);
            const windowKey = localDateTimeMinuteStr(windowDt);
            const massReset = windowTimes.filter((t) => t === windowKey).length >= 3;
            windowChangedTime = massReset ? "–" : shortTimeStr(windowDt, todayStr);
          }
        }
        if (!noWindow && hasLiveReason && !co2CloseException && (w === "on" || w === "off")) {
          highlightOk = (s.state === "on") === (w === "on");
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

      if (matchIcon === "🟢") green += 1;
      else if (matchIcon === "🟠") orange += 1;
      else if (matchIcon === "🔴") red += 1;

      // Offenes Fenster ohne Lüftungsbedarf: Farbe und Beschriftung folgen dem
      // Raumstatus des Backends (innerhalb der Schonfrist nur Hinweis).
      const noNeedHint = s.state === "off" && highlightCode === "no_need" && a.raumstatus === "hinweis";
      const highlightClass =
        co2CloseException || (comfortCloseResolvedException && highlightOk) || noWindowResolved
          ? "hl-green"
          : noWindow || highlightOk || noNeedHint
          ? "hl-orange"
          : "hl-red";

      const statusText = hasLiveReason ? (s.state === "on" ? "Öffnen" : noNeedHint ? "Hinweis" : "Schließen") : "–";
      let changedTime = "–";
      if (hasLiveReason && a.letzter_wechsel) {
        changedTime = shortTimeStr(new Date(a.letzter_wechsel), todayStr);
      }
      // Offenes Fenster ohne Lüftungsbedarf: "seit" meint das Öffnen des Fensters,
      // nicht den (längst vergangenen) Wechsel der Empfehlung.
      if (s.state === "off" && highlightCode === "no_need") changedTime = windowChangedTime;

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
      let absOpenGate = false;
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
        absOpenGate =
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
        const hInfo = heatingInfo(a, todayStr);
        for (const extra of [hInfo.since, hInfo.prevented, hInfo.override, hInfo.learned]) {
          if (extra) grund += ` <br>${parenBreak(extra)}`;
        }
        if (has(a, "heizung_zieltemperatur") && a.heizung_zieltemperatur !== null) {
          grund += ` <br>(Sollstellung: ${roundStr(a.heizung_zieltemperatur, 1)} °C)`;
        }
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|heat`, grund)}</td></tr>`;
        if ((has(a, "heizung_tagesplan") && Array.isArray(a.heizung_tagesplan)) || (has(a, "heizung_tagesverlauf") && Array.isArray(a.heizung_tagesverlauf))) {
          const planBlock = planHtml(a.heizung_tagesplan, undefined, false, a.heizung_tagesverlauf);
          if (planBlock) deviceRows += `<tr><td style="white-space:nowrap">Heizplan</td><td colspan="2">${planBlock}</td></tr>`;
        }
      }
      if (has(a, "duschen_erkannt")) {
        const name = ent(ents.dusche, `${a.duschen_erkannt ? "🟢" : "⚫"} Dusche`);
        let laufzeit = "–";
        if (a.duschen_erkannt && a.dusche_seit) {
          laufzeit = fmtDuration((Date.now() - new Date(a.dusche_seit).getTime()) / 60000);
        } else if (has(a, "dusche_letzte_laufzeit")) {
          laufzeit = fmtDuration(a.dusche_letzte_laufzeit);
        }
        let grund = a.duschen_erkannt ? "Luftfeuchtigkeit steigt schnell" : "–";
        if (has(a, "dusche_letzter_start") && a.dusche_letzter_start) {
          const startTxt = `Start ${shortTimeStr(new Date(a.dusche_letzter_start), todayStr)}`;
          grund = a.duschen_erkannt ? `${grund} <br>(${startTxt})` : `Letzter ${startTxt}`;
        }
        deviceRows += `<tr><td class="nw">${name}</td><td class="center nw">${laufzeit}</td><td>${cellDiv(`${a.raum}|shower`, grund)}</td></tr>`;
      }
      const deviceTable = deviceRows
        ? `<table class="values"><thead><tr><th>Gerät</th><th>Laufzeit</th><th>Status/Grund</th></tr></thead><tbody>${deviceRows}</tbody></table>`
        : "";

      const empfehlungText = hasLiveReason ? wrap(statusText, true) : statusText;

      // Ausführliche Begründung: eigene Zeile über die ganze Empfehlungs-Tabelle,
      // nur vorhanden, wenn ein aktueller Grund vorliegt (mehrere Öffnen-Gründe
      // stehen untereinander). Zahlen nur, soweit die Karte sie als Attribut hat.
      const numTxt = (v, d, unit) =>
        v === undefined || v === null || Number.isNaN(Number(v)) ? null : `${roundStr(v, d)} ${unit}`;
      const reasonSentence = (code, isOpen, withLabel = true) => {
        const label = withLabel ? `<span class="${highlightClass}">${esc(GRUND_TEXT[code] || code)}:</span>` : "";
        const tIn = numTxt(a.innentemperatur, 1, "°C");
        const tOut = numTxt(a.aussentemperatur, 1, "°C");
        const hIn = numTxt(a.luftfeuchtigkeit, 0, "%");
        const cIn = numTxt(a.co2, 0, "ppm");
        const tHi = numTxt(a.schwelle_temperatur_oeffnen, 1, "°C");
        const tLo = numTxt(a.schwelle_temperatur_schliessen, 1, "°C");
        const hHi = numTxt(a.schwelle_feuchtigkeit_oeffnen, 0, "%");
        const hLo = numTxt(a.schwelle_feuchtigkeit_schliessen, 0, "%");
        const cHi = numTxt(a.schwelle_co2_oeffnen, 0, "ppm");
        const cLo = numTxt(a.schwelle_co2_schliessen, 0, "ppm");
        const aIn = numTxt(a.absolute_luftfeuchtigkeit, 1, "g/m³");
        const aOut = numTxt(a.aussen_absolute_luftfeuchtigkeit, 1, "g/m³");
        let text = "";
        switch (code) {
          case "temp":
            text = isOpen
              ? `Die Raumtemperatur${tIn ? ` (${tIn})` : ""} liegt über der Obergrenze${tHi ? ` von ${tHi}` : ""}, Lüften kühlt den Raum.`
              : `Die Raumtemperatur${tIn ? ` (${tIn})` : ""} liegt unter der Untergrenze${tLo ? ` von ${tLo}` : ""}, weiteres Lüften kühlt zu stark aus.`;
            break;
          case "humidity":
            text = isOpen
              ? `Die Luftfeuchtigkeit${hIn ? ` (${hIn})` : ""} liegt über der Obergrenze${hHi ? ` von ${hHi}` : ""}.` +
                (aIn && aOut ? ` Die Außenluft ist absolut trockener (${aOut} gegen ${aIn} innen), Lüften entfeuchtet.` : "")
              : `Die Luftfeuchtigkeit${hIn ? ` (${hIn})` : ""} liegt unter der Untergrenze${hLo ? ` von ${hLo}` : ""}, weiteres Lüften ist nicht nötig.`;
            break;
          case "co2":
            text = isOpen
              ? `Der CO2-Wert${cIn ? ` (${cIn})` : ""} liegt über der Obergrenze${cHi ? ` von ${cHi}` : ""}, frische Luft ist nötig.`
              : `Der CO2-Wert${cIn ? ` (${cIn})` : ""} liegt unter der Untergrenze${cLo ? ` von ${cLo}` : ""}, die Luftqualität ist wieder gut.`;
            break;
          case "frost":
            text = `Die Außentemperatur${tOut ? ` (${tOut})` : ""} liegt an oder unter der Frostschutz-Grenze, das Fenster soll geschlossen bleiben.`;
            break;
          case "heat":
            text = `Die Außentemperatur${tOut ? ` (${tOut})` : ""} liegt an oder über der Hitzeschutz-Grenze, Lüften würde den Raum aufheizen.`;
            break;
          case "outdoor_warmer":
            text = `Die Außenluft${tOut ? ` (${tOut})` : ""} ist wärmer als die Obergrenze${tHi ? ` von ${tHi}` : ""}, Lüften würde den Raum aufheizen.`;
            break;
          case "outdoor_wetter":
            text = `Die Außenluft ist absolut feuchter${aIn && aOut ? ` (${aOut} gegen ${aIn} innen)` : ""}, Lüften würde die Feuchtigkeit erhöhen.`;
            break;
          case "duration":
            text = "Das Fenster war im Winter schon lange geöffnet, zum Energiesparen wird geschlossen.";
            break;
          case "no_need":
            text = noNeedHint
              ? "Das Fenster ist offen, obwohl aktuell kein Lüftungsbedarf besteht. Nach 30 Minuten wird Schließen empfohlen."
              : "Das Fenster ist schon länger offen, ohne dass Lüften nötig ist, zum Energiesparen wird Schließen empfohlen.";
            break;
          default:
            text = "";
        }
        return text ? (withLabel ? `${label} ${esc(text)}` : esc(text)) : label;
      };
      const reasonCodes = !hasLiveReason ? [] : s.state === "on" ? openReasons : [highlightCode];
      const reasonRow = reasonCodes.length
        ? `<tr class="reason-row"><td colspan="3">${reasonCodes.map((c) => reasonSentence(c, s.state === "on")).join("<br>")}</td></tr>`
        : "";

      // Statuszeilen für laufende Geräte (Luftentfeuchter/Klimaanlage): nur solange
      // das Gerät läuft; Uhrzeit = Start (aus *_seit), sonst "–".
      const deviceStatusRow = (entityId, name, on, since) => {
        if (on !== true) return "";
        const t = since ? shortTimeStr(new Date(since), todayStr) : "–";
        return `<tr><td>${ent(entityId, name)}</td><td class="nw">Aktiv</td><td class="nw">${t}</td></tr>`;
      };
      const deviceStatusRows =
        deviceStatusRow(ents.luftentfeuchter, "Luftentfeuchter", a.luftentfeuchter_an, a.luftentfeuchter_seit) +
        deviceStatusRow(ents.klimaanlage, "Klimaanlage", a.klimaanlage_an, a.klimaanlage_seit);

      let empfTable = "";
      if (!noWindow || deviceStatusRows) {
        const windowRows = noWindow
          ? ""
          : `<tr><td>${ent(windowEntity, "Fenster")}</td><td class="nw">${windowStateText}</td><td class="nw">${windowChangedTime}</td></tr>` +
            `<tr><td>${ent(id, "Empfehlung")}</td><td class="nw">${hasLiveReason ? empfehlungText : "–"}</td><td class="nw">${hasLiveReason ? changedTime : "–"}</td></tr>` +
            reasonRow;
        empfTable =
          `<table class="values"><thead><tr><th></th><th>Status</th><th>Uhrzeit</th></tr></thead><tbody>` +
          windowRows +
          deviceStatusRows +
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
        ? a.sprachausgabe_lautsprecher.map((t) => `<div class="tgt">${ent(t, breakable(esc(t)))}</div>`).join("")
        : "–";
      const n2Status = has(a, "app_aktiv") ? "🟢" : "⚫";
      const n2Ziel = has(a, "app_ziele")
        ? a.app_ziele.map((t) => `<div class="tgt">${ent(t, breakable(esc(t)))}</div>`).join("")
        : "–";
      const n3Status = has(a, "persistent_aktiv") ? "🟢" : "⚫";
      const notifyOpen = this._notifyOpenState.get(a.raum) || false;
      const notifyTable =
        `<details class="notify-details" data-notify-room="${esc(a.raum)}"${notifyOpen ? " open" : ""}><summary><strong>Benachrichtigungen</strong></summary>` +
        `<table class="values"><thead><tr><th>Benachrichtigung</th><th>Ziele</th></tr></thead><tbody>` +
        `<tr><td><div class="nrow"><span class="ni">${n1Status}</span><span>Sprachausgabe</span></div></td><td>${n1Ziel === "–" ? n1Ziel : cellDiv(`${a.raum}|n1`, n1Ziel)}</td></tr>` +
        `<tr><td><div class="nrow"><span class="ni">${n2Status}</span><span>Push-Benachrichtigung</span></div></td><td>${n2Ziel === "–" ? n2Ziel : cellDiv(`${a.raum}|n2`, n2Ziel)}</td></tr>` +
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
      // compact_room (vom Raum-Dialog gesetzt, siehe openRoomDialog): der
      // einzelne Raum startet immer aufgeklappt - im Dialog will man ja
      // gerade die Details sehen.
      const compact = this._config.compact_room === true;
      const defaultOpen =
        compact || (statusClass !== "status-green" && this._config.expand_attention_rooms !== false);
      const storedRoomState = this._roomOpenState.get(a.raum);
      const isOpen =
        storedRoomState && storedRoomState.statusClass === statusClass
          ? storedRoomState.open
          : defaultOpen;
      this._roomOpenState.set(a.raum, { statusClass, open: isOpen });

      if (compact) {
        entries.push({
          sortKey: `0${a.raum}`,
          html: crCompactRoom({
            a, ents, ent, id, expandedCells: this._expandedCells, todayStr,
            status: a.raumstatus, noWindow, windowEntity,
            windowState: windowEntity && states[windowEntity] ? states[windowEntity].state : "",
            windowChangedTime, hasLiveReason, statusText, changedTime, highlightClass,
            reasonText: reasonCodes.map((cd) => reasonSentence(cd, s.state === "on", false)).join(" "),
            highlightTemp, highlightHum, highlightCo2, absOpenGate, tempLo, tempHi, notifyOpen,
            planOpen: this._planOpen.has(a.raum),
            devOpen: this._devOpen.get(a.raum),
            headerOut: this._headerSink ? headerOut : null,
            notifyOut,
            thermo: !!this._thermoEl,
          }),
        });
        continue;
      }

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
    this._compactHeader = this._headerSink && headerOut.name ? Object.assign({}, headerOut) : null;
    this._compactNotify = notifyOut && typeof notifyOut.html === "string" ? notifyOut.html : null;

    // compact_room: nur der Raum, ohne Übersicht und Außen-Messwerte.
    this._content.innerHTML =
      this._config.compact_room === true
        ? roomsHtml
        : `<div class="overview-wrap">${overviewTable}${outdoorTable}</div>${roomsHtml}`;
    // Dauerhaftes Thermostat-Element (Raum-Dialog) wieder in seinen Platz setzen.
    if (this._thermoEl) {
      const slot = this._content.querySelector(".cr-thermo-slot");
      if (slot) slot.appendChild(this._thermoEl);
    }
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
      /* Ausführliche Begründung: eine Zeile über die ganze Tabelle, normaler
         Zeilenumbruch nur an Leerzeichen. */
      table.values tr.reason-row td { overflow-wrap: normal; word-break: normal; white-space: normal; }
      .notify-details table.values { margin-top: 8px; margin-bottom: 4px; }
      /* Methodennamen nur an Leerzeichen/Bindestrichen umbrechen, nie mitten im Wort -
         die Ziele-Spalte bricht dagegen an . und _ (siehe breakable()). */
      .notify-details table.values th:first-child,
      .notify-details table.values td:first-child { overflow-wrap: normal; word-break: normal; }
      /* Ziele stehen untereinander - die Spalte bekommt Vorrang, die Methodennamen
         brechen dafür an Leerzeichen/Bindestrichen um. */
      .notify-details .tgt + .tgt { margin-top: 4px; }
      .notify-details table.values th:nth-child(2),
      .notify-details table.values td:nth-child(2) { width: 62%; }
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

      /* Kompakte Raumansicht (Raum-Dialog, compact_room): Home-Assistant-Stil */
      ha-card.sc-compact { box-shadow: none; border: none; background: transparent; }
      ha-card.sc-compact .smart-climate-card-content { padding: 4px 20px 10px; }
      .cr-top { display: flex; align-items: center; gap: 8px; margin: 0 4px 4px; padding-right: 40px; }
      .cr-top h1 { flex: 1; margin: 0; font-size: 1.35em; font-weight: 500; min-width: 0; overflow-wrap: anywhere; }
      .cr-hchip {
        display: inline-flex; align-items: center; gap: 6px; flex: none;
        border-radius: 999px; padding: 3px 10px 3px 7px; font-size: 0.85em; font-weight: 500;
        color: var(--c); background: rgba(127, 127, 127, 0.18);
        background: color-mix(in srgb, var(--c) 18%, transparent);
      }
      .cr-hchip i { width: 7px; height: 7px; border-radius: 50%; background: var(--c); display: block; }
      .cr-sec + .cr-sec { margin-top: 8px; }
      .cr-devs { display: flex; gap: 4px; padding: 10px 0 8px; }
      .cr-dev {
        flex: 1 1 0; min-width: 0; background: none; border: 0; padding: 2px 0; margin: 0; font: inherit; color: inherit;
        cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 3px; -webkit-tap-highlight-color: transparent;
      }
      .cr-dev .cr-ico { width: 44px; height: 44px; --mdc-icon-size: 24px; }
      .cr-dev.open .cr-ico { box-shadow: 0 0 0 2px var(--c); }
      .cr-dv { font-weight: 500; white-space: nowrap; }
      .cr-dn { font-size: 0.8em; color: var(--secondary-text-color, #727272); max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .cr-devdetail { display: none; border-top: 1px solid var(--divider-color, #e0e0e0); padding: 8px 2px 10px; cursor: pointer; }
      .cr-devdetail.open { display: block; }
      .cr-sec { background: transparent; border: 1px solid var(--divider-color, rgba(127, 127, 127, 0.35)); border-radius: 14px; padding: 0 10px; }
      .cr-row { display: flex; align-items: center; gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .cr-row:last-child { border-bottom: 0; }
      .cr-row.cr-link { cursor: pointer; }
      .cr-ico {
        width: 32px; height: 32px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center;
        color: var(--c); background: rgba(127, 127, 127, 0.18);
        background: color-mix(in srgb, var(--c) 20%, transparent);
        --mdc-icon-size: 20px;
      }
      .cr-t { flex: 1; min-width: 0; }
      .cr-p { font-size: 1em; }
      .cr-s { font-size: 0.85em; color: var(--secondary-text-color, #727272); }
      .cr-v { font-weight: 500; white-space: nowrap; }
      .cr-chip {
        border-radius: 999px; padding: 2px 11px; font-size: 0.88em; font-weight: 500; white-space: nowrap;
        color: var(--c); background: rgba(127, 127, 127, 0.18);
        background: color-mix(in srgb, var(--c) 20%, transparent);
      }
      .cr-clamp { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2; overflow: hidden; cursor: pointer; }
      .cr-clamp.expanded { display: block; -webkit-line-clamp: unset; line-clamp: unset; overflow: visible; }
      .cr-gl { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
      .cr-bar { position: relative; height: 5px; border-radius: 3px; background: var(--divider-color, #cfcfcf); margin: 6px 0 2px; }
      .cr-band { position: absolute; top: 0; bottom: 0; border-radius: 3px; background: var(--success-color, #4caf50); opacity: 0.55; }
      .cr-mk {
        position: absolute; top: 50%; width: 11px; height: 11px; border-radius: 50%; background: var(--c);
        transform: translate(-50%, -50%); border: 2px solid var(--secondary-background-color, #fff); box-sizing: content-box;
      }
      .cr-xtra { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; column-gap: 8px; margin-top: 4px; padding-bottom: 2px; line-height: 1.3; }
      .cr-xtra .nw { white-space: nowrap; }
      .cr-thermo-slot { border-top: 1px solid var(--divider-color, #e0e0e0); padding: 8px 0 8px; }
      .plan { width: 100%; min-width: 0; padding: 2px 0; }
      .plan-wrap { position: relative; }
      .plan-bar { display: flex; height: 14px; border-radius: 7px; overflow: hidden; background: var(--divider-color, #e0e0e0); }
      .plan-seg { height: 100%; min-width: 0; }
      .plan-fut { opacity: 0.6; }
      .plan-none { background: repeating-linear-gradient(45deg, rgba(127, 127, 127, 0.35) 0 4px, transparent 4px 8px); }
      .plan-now { position: absolute; top: -3px; bottom: -3px; width: 2px; margin-left: -1px; border-radius: 1px; background: var(--primary-text-color, #000); }
      .plan-scale { position: relative; height: 1.2em; margin-top: 3px; font-size: 0.75em; color: var(--secondary-text-color, #727272); }
      .plan-scale span { position: absolute; transform: translateX(-50%); }
      .plan-times { margin-top: 2px; font-size: 0.85em; line-height: 1.5; color: var(--secondary-text-color, #727272); }
      .plan-t { display: inline-block; margin-right: 12px; white-space: nowrap; }
      .plan-dot { display: inline-block; width: 8px; height: 8px; margin-right: 4px; border-radius: 50%; }
      .cr-plan .cr-t { min-width: 0; }
      .cr-plansum { display: flex; align-items: center; justify-content: space-between; gap: 10px; cursor: pointer; }
      .cr-planfold.open .cr-chev { transform: rotate(90deg); }
      .cr-planfold:not(.open) .plan-times { display: none; }
      .cr-v.cr-big { font-size: 1.6em; line-height: 1.1; }
      .cr-v.cr-gv { flex: none; width: 6.4em; text-align: right; }
      .cr-v.cr-gv.cr-big { width: 4em; }
      .cr-notify > summary { list-style: none; cursor: pointer; }
      .cr-notify > summary::-webkit-details-marker { display: none; }
      .cr-fold { display: flex; align-items: center; gap: 10px; padding: 8px 0; }
      .cr-ft { flex: 1; }
      .cr-chev { color: var(--secondary-text-color, #727272); transition: transform 0.15s ease; }
      .cr-notify[open] .cr-chev { transform: rotate(90deg); }
      .cr-notify .cr-row { border-top: 1px solid var(--divider-color, #e0e0e0); border-bottom: 0; }
    `;
  }

  static getStubConfig() {
    return {};
  }
}

if (!customElements.get("smart-climate-card")) {
  customElements.define("smart-climate-card", SmartClimateCard);
}

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

if (!customElements.get("smart-climate-card-editor")) {
  customElements.define("smart-climate-card-editor", SmartClimateCardEditor);
}

/*
 * Raum-Dialog: Tippen auf einen Raumnamen im Dashboard öffnet die Details
 * dieses einen Raums. Auslöser ist die Standard-Tipp-Aktion `fire-dom-event`
 * (Home Assistant sendet dafür das Ereignis "ll-custom" mit der
 * Aktions-Konfiguration als detail), z. B. an einer Mushroom-/Bubble-Karte:
 *
 *   tap_action:
 *     action: fire-dom-event
 *     smart_climate_room: badezimmer   # Raumname, Slug oder Entity-ID
 *
 * Gegenüber einem Pop-up je Raum wird der Inhalt erst beim Tippen erzeugt und
 * beim Schließen wieder entfernt - es läuft nichts im Hintergrund mit.
 */
function scSlug(text) {
  return String(text)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ß/g, "ss")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function scFindRoomEntity(hass, key) {
  const states = hass.states;
  const raw = String(key).trim();
  if (raw.includes(".")) return states[raw] ? raw : null;
  const slug = scSlug(raw);
  for (const id of Object.keys(states)) {
    if (!id.startsWith("binary_sensor.")) continue;
    const attrs = states[id].attributes;
    if (!attrs || !has(attrs, "raum")) continue;
    if (scSlug(attrs.raum) === slug) return id;
  }
  return null;
}

let scRoomDialog = null;

// ---------------------------------------------------------------------------
// Gesamtübersicht (im selben Dialog wie die Raumansicht): Zähler, Außenwerte und
// eine kompakte Zeile je Raum. Tippen auf eine Zeile öffnet den Raum-Dialog; dort
// führt der Knopf in der Kopfzeile wieder hierher.
// ---------------------------------------------------------------------------
const SC_OVERVIEW_KEY = "__overview__";
const SC_STATUS_ICON = { ok: "mdi:check-circle-outline", hinweis: "mdi:alert-circle-outline", handlungsbedarf: "mdi:alert-outline" };

function scRoomIds(hass) {
  const out = [];
  for (const id of Object.keys(hass.states)) {
    if (!id.startsWith("binary_sensor.")) continue;
    const a = hass.states[id].attributes;
    if (a && has(a, "raum") && has(a, "integration_version") && has(a, "raumstatus")) out.push(id);
  }
  return out;
}

// Liefert { head, foot, rooms: [{id, html}], worst, count } für die Übersicht
// (html = Inhalt der Zeile eines Raums ohne Rahmen).
function scOverview(hass) {
  const ids = scRoomIds(hass);
  const rank = { handlungsbedarf: 0, hinweis: 1, ok: 2 };
  ids.sort((x, y) => {
    const ax = hass.states[x].attributes;
    const ay = hass.states[y].attributes;
    const d = (rank[ax.raumstatus] ?? 2) - (rank[ay.raumstatus] ?? 2);
    return d || String(ax.raum).localeCompare(String(ay.raum));
  });
  const n = { ok: 0, hinweis: 0, handlungsbedarf: 0 };
  let version = null;
  let summer = null;
  const outdoor = { temp: null, hum: null, abs: null, dew: null };
  const rooms = [];
  for (const id of ids) {
    const s = hass.states[id];
    const a = s.attributes;
    const st = has(rank, a.raumstatus) ? a.raumstatus : "ok";
    n[st] += 1;
    if (version === null) version = a.integration_version;
    if (summer === null && has(a, "sommermodus_an")) summer = a.sommermodus_an;
    for (const [k, attr] of [["temp", "aussentemperatur"], ["hum", "aussen_luftfeuchtigkeit"], ["abs", "aussen_absolute_luftfeuchtigkeit"], ["dew", "aussen_taupunkt"]]) {
      if (outdoor[k] === null && has(a, attr) && a[attr] !== null) outdoor[k] = a[attr];
    }
    const ents = a.entitaeten || {};
    const noWindow = has(a, "hat_fenster") && a.hat_fenster === false;
    const w = ents.fenster && hass.states[ents.fenster] ? hass.states[ents.fenster].state : "";
    const subs = [];
    if (!noWindow && (w === "on" || w === "off")) subs.push(w === "on" ? "Fenster offen" : "Fenster zu");
    const code = s.state === "on" ? (a.offene_gruende || [])[0] || "" : a.schliessgrund_live || "";
    if (code) subs.push(s.state === "on" ? "Öffnen" : code === "no_need" && st === "hinweis" ? "Fenster ohne Bedarf offen" : "Schließen");
    const color = SC_STATUS_COLOR[st];
    const vals = [];
    if (a.innentemperatur !== undefined && a.innentemperatur !== null) vals.push(`${roundStr(a.innentemperatur, 1)} °C`);
    if (has(a, "luftfeuchtigkeit") && a.luftfeuchtigkeit !== null) vals.push(`${roundStr(a.luftfeuchtigkeit, 0)} %`);
    if (has(a, "co2") && a.co2 !== null) vals.push(`${roundStr(a.co2, 0)} ppm`);
    const dev = [];
    if (has(a, "heizung_an")) {
      const hc = SC_HEATING_COLOR[a.heizung_modus] || SC_COLOR.grey;
      const label = (HEATING_MODE_LABEL[a.heizung_modus] || {}).text || "Heizung";
      dev.push(`<span class="ov-dev" style="color:${hc}" title="Heizung: ${esc(label)}"><ha-icon icon="mdi:radiator"></ha-icon></span>`);
    }
    if (a.luftentfeuchter_an === true) dev.push(`<span class="ov-dev" style="color:${SC_COLOR.blue}" title="Luftentfeuchter läuft"><ha-icon icon="mdi:air-humidifier"></ha-icon></span>`);
    if (a.klimaanlage_an === true) dev.push(`<span class="ov-dev" style="color:${SC_COLOR.blue}" title="Klimaanlage läuft"><ha-icon icon="mdi:snowflake"></ha-icon></span>`);
    if (a.duschen_erkannt === true) dev.push(`<span class="ov-dev" style="color:${SC_COLOR.blue}" title="Dusche aktiv"><ha-icon icon="mdi:shower-head"></ha-icon></span>`);
    const planRow = has(a, "heizung_tagesplan") || has(a, "heizung_tagesverlauf") ? planHtml(a.heizung_tagesplan, undefined, true, a.heizung_tagesverlauf) : "";
    rooms.push({
      id,
      html:
        `<span class="ov-ico" style="--c:${color}"><ha-icon icon="${SC_STATUS_ICON[st]}"></ha-icon></span>` +
        `<span class="ov-t"><span class="ov-n">${esc(a.raum)}</span>${subs.length ? `<span class="ov-s">${esc(subs.join(" · "))}</span>` : ""}</span>` +
        `<span class="ov-r"><span class="ov-vals">${vals.map(esc).join(" · ")}</span>${dev.length ? `<span class="ov-devs">${dev.join("")}</span>` : ""}</span>` +
        `<ha-icon class="ov-chev" icon="mdi:chevron-right"></ha-icon>` +
        (planRow ? `<span class="ov-plan">${planRow}</span>` : ""),
    });
  }
  const cnt = (cls, label, v, color) =>
    `<div class="ov-cnt"><i style="background:${color}"></i><b>${v}</b><span>${label}</span></div>`;
  let head =
    `<div class="ov-counts">${cnt("r", "Handeln", n.handlungsbedarf, SC_COLOR.red)}${cnt("o", "Hinweis", n.hinweis, SC_COLOR.orange)}${cnt("g", "OK", n.ok, SC_COLOR.green)}</div>`;
  const tiles = [
    ["Außen", outdoor.temp !== null ? `${roundStr(outdoor.temp, 1)} °C` : "–"],
    ["Luftfeuchtigkeit", outdoor.hum !== null ? `${roundStr(outdoor.hum, 0)} %` : "–"],
    ["Abs. Luftfeuchtigkeit", outdoor.abs !== null ? `${outdoor.abs} g/m³` : "–"],
    ["Taupunkt", outdoor.dew !== null ? `${roundStr(outdoor.dew, 1)} °C` : "–"],
  ];
  head +=
    `<div class="ov-sec">Außenwerte</div><div class="ov-tiles">${tiles.map(([l, v]) => `<div class="ov-tile"><span>${l}</span><b>${v}</b></div>`).join("")}</div>`;
  const worst = n.handlungsbedarf ? "handlungsbedarf" : n.hinweis ? "hinweis" : "ok";
  let foot = "";
  const meta = [];
  if (summer !== null) meta.push(summer ? "☀️ Sommermodus" : "❄️ Wintermodus");
  if (version !== null) meta.push(`Version ${esc(version)}`);
  if (meta.length) foot = `<div class="ov-foot">${meta.join(" · ")}</div>`;
  return { head, foot, rooms, worst, count: ids.length };
}

// Eigene Thermostat-Bedienung der Heizung (Ist-Temperatur, Sollwert mit -/+,
// Betriebsmodus und Voreinstellung) über die Standard-Dienste der climate-
// Entität. Home Assistants eigene Thermostat-Karte blieb im Dialog leer, daher
// kein Einbetten. Liefert eine Funktion, die bei neuem hass aufzurufen ist.
const SC_HVAC_LABEL = {
  off: "Aus", heat: "Heizbetrieb", cool: "Kühlen", auto: "Auto", heat_cool: "Heizen/Kühlen",
  dry: "Trocknen", fan_only: "Lüfter",
};
const SC_PRESET_LABEL = {
  comfort: "Komfort", eco: "Eco", home: "Zuhause", sleep: "Schlafen", away: "Abwesend",
  boost: "Boost", activity: "Aktivität", none: "Keine", building_protection: "Gebäudeschutz",
};

function scLabel(map, key) {
  if (has(map, key)) return map[key];
  const text = String(key).replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const SC_OPTIMISTIC_MS = 8000;

const SC_SVG_MINUS = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M19,13H5V11H19V13Z"/></svg>';
const SC_SVG_PLUS = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>';

function scBuildThermostat(container, heatingId, root) {
  let pending = null;
  let timer = null;
  let sig = "";
  let last = null;
  // Sofortige Rückmeldung (Lektion 160): ein getipptes Preset/ein Betriebsmodus gilt
  // sofort als aktiv, bis das Gerät es bestätigt, höchstens SC_OPTIMISTIC_MS lang.
  const opt = { preset: null, mode: null };
  const optTimer = { preset: null, mode: null };
  const clearOpt = (kind) => {
    clearTimeout(optTimer[kind]);
    optTimer[kind] = null;
    opt[kind] = null;
  };
  const call = (service, data) => {
    const h = root.hass;
    if (!h || !h.callService) return null;
    return h.callService("climate", service, Object.assign({ entity_id: heatingId }, data));
  };
  const render = (hass) => {
    const st = hass && hass.states && hass.states[heatingId];
    last = st;
    if (!st) {
      container.innerHTML = "";
      return;
    }
    const a = st.attributes || {};
    const target = pending !== null ? pending : a.temperature;
    // Bestätigt das Gerät den angenommenen Wert, entfällt die Annahme.
    if (opt.preset !== null && a.preset_mode === opt.preset) clearOpt("preset");
    if (opt.mode !== null && st.state === opt.mode) clearOpt("mode");
    const shownPreset = opt.preset !== null ? opt.preset : a.preset_mode;
    const shownMode = opt.mode !== null ? opt.mode : st.state;
    const next = JSON.stringify([st.state, a.current_temperature, a.temperature, a.hvac_action, a.preset_mode, a.hvac_modes, a.preset_modes, a.target_temp_step, a.min_temp, a.max_temp, pending, opt.preset, opt.mode]);
    if (next === sig) return;
    sig = next;
    const unavailable = st.state === "unavailable" || st.state === "unknown";
    let html = '<div class="sc-th">';
    // Die Ist-Temperatur steht in der Zeile "Temperatur" darüber; Bezeichnung und Zustand
    // (Heizt/Leerlauf) entfallen; beim Heizen glüht ein Farbverlauf hinter dem Sollwert.
    const heating = a.hvac_action === "heating";
    if (unavailable) html += '<div class="sc-th-top"><span>Heizung nicht verfügbar</span></div>';
    if (!unavailable && target !== undefined && target !== null) {
      html += `<div class="sc-th-set${heating ? " heating" : ""}"><button type="button" class="sc-th-btn" data-th="minus" aria-label="Kälter">${SC_SVG_MINUS}</button><div class="sc-th-val" data-th="more" role="button" aria-label="Details der Heizung">${scSetpointHtml(target)}</div><button type="button" class="sc-th-btn" data-th="plus" aria-label="Wärmer">${SC_SVG_PLUS}</button></div>`;
    }
    const chips = (list, active, kind, map) =>
      `<div class="sc-th-chips${list.length > 4 ? " wrap" : ""}">` +
      list.map((m) => { const mc = kind === "preset" && m === active ? SC_HEATING_COLOR[scPresetMode(m)] : ""; return `<button type="button" class="sc-th-chip${m === active ? " on" : ""}${mc ? " mc" : ""}"${mc ? ` style="--mc:${mc}"` : ""} data-th="${kind}" data-v="${esc(m)}">${esc(scLabel(map, m))}</button>`; }).join("") +
      "</div>";
    if (!unavailable && Array.isArray(a.hvac_modes) && a.hvac_modes.length > 1) html += chips(a.hvac_modes, shownMode, "mode", SC_HVAC_LABEL);
    if (!unavailable && Array.isArray(a.preset_modes) && a.preset_modes.length > 0) html += chips(a.preset_modes, shownPreset, "preset", SC_PRESET_LABEL);
    html += "</div>";
    container.innerHTML = html;
  };
  container.addEventListener("click", (ev) => {
    const btn = ev.target && ev.target.closest ? ev.target.closest("[data-th]") : null;
    if (!btn || !last) return;
    const a = last.attributes || {};
    const kind = btn.dataset.th;
    if (kind === "more") {
      // Tippen auf den Sollwert öffnet die Standardansicht der Heizungs-Entität; der
      // Raum-Dialog leitet das Ereignis weiter und schließt sich dabei.
      container.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: heatingId }, bubbles: true, composed: true }));
      return;
    }
    if (kind === "minus" || kind === "plus") {
      const step = Number(a.target_temp_step) > 0 ? Number(a.target_temp_step) : 0.5;
      const cur = pending !== null ? pending : Number(a.temperature);
      if (Number.isNaN(cur)) return;
      let v = Math.round((cur + (kind === "plus" ? step : -step)) / step) * step;
      if (Number.isFinite(Number(a.min_temp))) v = Math.max(Number(a.min_temp), v);
      if (Number.isFinite(Number(a.max_temp))) v = Math.min(Number(a.max_temp), v);
      pending = Math.round(v * 100) / 100;
      sig = "";
      render(root.hass);
      clearTimeout(timer);
      timer = setTimeout(() => {
        const t = pending;
        pending = null;
        call("set_temperature", { temperature: t });
      }, 700);
    } else if (kind === "mode" || kind === "preset") {
      const key = kind === "mode" ? "mode" : "preset";
      const value = btn.dataset.v;
      // Ein bereits aktives Preset wird bewusst erneut gesetzt: das verwirft eine von Hand
      // geänderte Solltemperatur (Lektion 160). Nur der Betriebsmodus wird nicht wiederholt.
      if (key === "mode" && last.state === value && opt.mode === null) return;
      clearOpt(key);
      opt[key] = value;
      optTimer[key] = setTimeout(() => {
        clearOpt(key);
        sig = "";
        render(root.hass);
      }, SC_OPTIMISTIC_MS);
      sig = "";
      render(root.hass);
      const res = kind === "mode" ? call("set_hvac_mode", { hvac_mode: value }) : call("set_preset_mode", { preset_mode: value });
      if (res && typeof res.catch === "function") {
        res.catch(() => {
          clearOpt(key);
          sig = "";
          render(root.hass);
        });
      }
    }
  });
  render(root.hass);
  return { update: render, stop: () => { clearTimeout(timer); clearOpt("preset"); clearOpt("mode"); } };
}

// Eine more-info-Anfrage für einen Raum-Sensor dieser Integration öffnet statt
// des Standard-Fensters den Raum-Dialog. Das Standard-Fenster bleibt über den
// Link "Standardansicht" (scBypass) erreichbar.
function scInterceptMoreInfo(ev) {
  const detail = ev && ev.detail;
  if (!detail || detail.scBypass || !detail.entityId) return;
  const root = document.querySelector("home-assistant");
  const hass = root && root.hass;
  if (!hass) return;
  const state = hass.states[detail.entityId];
  if (
    !state ||
    !String(detail.entityId).startsWith("binary_sensor.") ||
    !state.attributes ||
    !has(state.attributes, "raum") ||
    !has(state.attributes, "integration_version")
  ) {
    return;
  }
  // Anfragen aus dem Raum-Dialog selbst (Bezeichnungen) gehen unverändert durch.
  const path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
  if (path.some((n) => n && n.classList && n.classList.contains("sc-room-dialog"))) return;
  ev.stopImmediatePropagation();
  ev.stopPropagation();
  openRoomDialog(detail.entityId);
}

function scCloseRoomDialog() {
  if (!scRoomDialog) return;
  clearInterval(scRoomDialog.timer);
  if (scRoomDialog.thermoCtl) scRoomDialog.thermoCtl.stop();
  if (scRoomDialog.cleanup) scRoomDialog.cleanup();
  document.removeEventListener("keydown", scRoomDialog.onKey, true);
  document.removeEventListener("wheel", scRoomDialog.onWheel, true);
  document.removeEventListener("touchstart", scRoomDialog.onLockStart, true);
  document.removeEventListener("touchmove", scRoomDialog.onLockMove, true);
  scRoomDialog.overlay.remove();
  // Scrollposition der Seite sichern wiederherstellen (Lektion 161)
  const sp = scRoomDialog.pageScroll;
  if (sp && (window.scrollX !== sp.x || window.scrollY !== sp.y)) window.scrollTo(sp.x, sp.y);
  scRoomDialog = null;
}

function openRoomDialog(key) {
  const root = document.querySelector("home-assistant");
  const hass = root && root.hass;
  if (!hass) return;
  scCloseRoomDialog();

  const overviewMode = key === SC_OVERVIEW_KEY;
  const overlay = document.createElement("div");
  overlay.className = "sc-room-dialog";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.innerHTML =
    "<style>" +
    ".sc-room-dialog{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:flex-end;justify-content:center;padding:0;background:rgba(0,0,0,.55);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);box-sizing:border-box;overscroll-behavior:contain;touch-action:none;animation:sc-fade .2s ease-out}" +
    ".sc-room-panel{position:relative;display:flex;flex-direction:column;width:100%;max-width:600px;height:calc(100% - max(env(safe-area-inset-top,0px),8px));max-height:calc(100% - max(env(safe-area-inset-top,0px),8px));overflow:hidden;border-radius:28px 28px 0 0;border:1px solid var(--divider-color,rgba(127,127,127,.45));border-bottom:0;box-shadow:0 -6px 28px rgba(0,0,0,.45);background:var(--ha-dialog-surface-background,var(--mdc-theme-surface,var(--card-background-color,#fff)));color:var(--primary-text-color,#000);box-sizing:border-box;animation:sc-up .24s ease-out}" +
    "@keyframes sc-up{from{transform:translateY(40px);opacity:0}to{transform:none;opacity:1}}" +
    "@keyframes sc-fade{from{opacity:0}to{opacity:1}}" +
    ".sc-room-grip{position:absolute;top:7px;left:50%;width:40px;height:4px;margin-left:-20px;border-radius:2px;background:var(--divider-color,rgba(127,127,127,.6));opacity:.9;pointer-events:none;z-index:3}.sc-room-scroll{padding-bottom:env(safe-area-inset-bottom,0px);overflow:auto;flex:1 1 auto;min-height:0;overscroll-behavior:contain;touch-action:pan-y;-webkit-overflow-scrolling:touch}" +
    ".sc-room-bar{flex:none;position:relative;z-index:2;display:flex;align-items:center;gap:2px;padding:18px 8px 2px}" +
    ".sc-room-close,.sc-room-std,.sc-room-list{width:44px;height:44px;border:0;border-radius:50%;background:transparent;color:var(--primary-text-color,#000);cursor:pointer;flex:none;padding:0;display:flex;align-items:center;justify-content:center;line-height:1;font-size:22px;--mdc-icon-size:24px}" +
    ".sc-room-bell{width:44px;height:44px;border:0;border-radius:50%;background:transparent;color:var(--primary-text-color,#000);cursor:pointer;flex:none;padding:0;display:flex;align-items:center;justify-content:center;--mdc-icon-size:24px}" +
    ".sc-room-bell.open{background:rgba(127,127,127,.2)}" +
    ".sc-room-menu{display:none;position:absolute;right:12px;top:var(--mt,64px);z-index:6;width:min(320px,calc(100% - 24px));max-height:calc(100% - var(--mt,64px) - 16px);overflow:auto;box-sizing:border-box;padding:2px 14px;border:1px solid var(--divider-color,rgba(127,127,127,.45));border-radius:14px;background:var(--ha-dialog-surface-background,var(--mdc-theme-surface,var(--card-background-color,#fff)));box-shadow:0 8px 28px rgba(0,0,0,.5)}" +
    ".sc-room-menu.open{display:block}" +
    ".sc-room-menu .cr-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--divider-color,rgba(127,127,127,.35))}.sc-room-menu .cr-row:last-child{border-bottom:0}" +
    ".sc-room-menu .cr-ico{width:32px;height:32px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;color:var(--c);background:rgba(127,127,127,.18);background:color-mix(in srgb,var(--c) 20%,transparent);--mdc-icon-size:20px}" +
    ".sc-room-menu .cr-t{flex:1;min-width:0}.sc-room-menu .cr-p{font-size:15px}.sc-room-menu .cr-s{font-size:13px;color:var(--secondary-text-color,#727272)}.sc-room-menu .cr-v{font-weight:500;white-space:nowrap}.sc-room-menu [data-entity]{cursor:pointer}" +
    ".sc-room-title{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;padding:0 6px;min-height:48px}" +
    ".sc-room-sub{display:flex;align-items:center;gap:6px;font-size:13px;line-height:1.25;color:var(--secondary-text-color,#727272);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".sc-room-sub i{width:7px;height:7px;border-radius:50%;background:var(--c);display:block;flex:none}.sc-room-sub b{font-weight:500;color:var(--c)}" +
    ".sc-room-title h1{margin:0;font-size:20px;font-weight:500;line-height:1.2;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".sc-th{padding:0;display:flex;flex-direction:column;gap:8px}" +
    ".sc-th-top{display:flex;justify-content:space-between;font-size:14px;padding:0 8px;color:var(--primary-text-color,#000);opacity:.8}" +
    ".sc-th-set{position:relative;display:flex;align-items:center;justify-content:center;gap:24px}" +
    ".sc-th-set>*{position:relative;z-index:1}" +
    ".sc-th-set.heating::before{content:\"\";position:absolute;left:-10px;right:-10px;top:-26px;bottom:-26px;z-index:0;pointer-events:none;background:radial-gradient(ellipse at center,rgba(255,140,58,.32) 0,rgba(255,140,58,.1) 48%,rgba(255,140,58,0) 74%);background:radial-gradient(ellipse at center,color-mix(in srgb,var(--state-climate-heat-color,#ff8c3a) 34%,transparent) 0,color-mix(in srgb,var(--state-climate-heat-color,#ff8c3a) 11%,transparent) 48%,transparent 74%)}" +
    ".sc-th-val{cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;line-height:1;min-width:130px;white-space:nowrap}" +
    ".sc-th-num{font-size:72px;font-weight:400}" +
    ".sc-th-side{display:flex;flex-direction:column;gap:6px;align-items:flex-start}" +
    ".sc-th-val small{font-size:22px;font-weight:400;color:var(--secondary-text-color,#727272)}" +
    ".sc-th-val .sc-th-dec{font-size:28px;color:inherit}" +
    "@media (max-width:340px){.sc-th-set{gap:12px}}" +
    ".sc-th-btn{width:48px;height:48px;border-radius:50%;border:1px solid var(--secondary-text-color,#9b9b9b);background:transparent;color:var(--secondary-text-color,#9b9b9b);padding:0;display:flex;align-items:center;justify-content:center;cursor:pointer}" +
    ".sc-th-chips{display:flex;flex-wrap:nowrap;gap:5px;justify-content:center}" +
    ".sc-th-chips.wrap{flex-wrap:wrap;gap:8px}" +
    ".sc-th-chip{flex:1 1 auto;min-width:0;border:1px solid var(--divider-color,#999);border-radius:16px;background:transparent;color:inherit;padding:7px 5px;font-size:clamp(10.5px,3.3vw,14px);white-space:nowrap;text-align:center;cursor:pointer}" +
    ".sc-th-chips.wrap .sc-th-chip{flex:0 1 auto;padding:6px 14px;font-size:14px}" +
    ".sc-th-chip.on{background:var(--primary-color,#03a9f4);border-color:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}" +
    ".sc-th-chip.on.mc{background:var(--mc);border-color:var(--mc);color:#1b1b1b}" +
    ".sc-room-thermo-fb{display:flex;align-items:center;justify-content:center;gap:12px;padding:8px 16px}" +
    ".sc-room-thermo-fb button{border:1px solid var(--divider-color,#999);border-radius:18px;background:transparent;color:inherit;padding:8px 16px;font-size:15px;cursor:pointer}" +
    ".sc-room-missing{padding:8px 16px 24px}" +
    ".ov{padding:0 20px 16px}" +
    ".ov-counts{display:flex;gap:8px;margin:2px 0 4px}" +
    ".ov-cnt{flex:1 1 0;min-width:0;display:flex;align-items:center;gap:6px;padding:10px 10px;border:1px solid var(--divider-color,rgba(127,127,127,.35));border-radius:14px;background:transparent}" +
    ".ov-cnt i{width:9px;height:9px;border-radius:50%;flex:none}.ov-cnt b{font-size:18px;font-weight:600}.ov-cnt span{font-size:12px;color:var(--secondary-text-color,#727272);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}" +
    ".ov-sec{margin:14px 4px 6px;font-size:12px;font-weight:500;letter-spacing:.04em;text-transform:uppercase;color:var(--secondary-text-color,#727272)}" +
    ".ov-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}" +
    "@media (min-width:520px){.ov-tiles{grid-template-columns:repeat(4,minmax(0,1fr))}}" +
    ".ov-tile{padding:8px 12px;border:1px solid var(--divider-color,rgba(127,127,127,.35));border-radius:14px;background:transparent;display:flex;flex-direction:column;gap:2px;min-width:0}" +
    ".ov-tile span{font-size:12px;color:var(--secondary-text-color,#727272);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ov-tile b{font-size:16px;font-weight:600}" +
    ".ov-list{border:1px solid var(--divider-color,rgba(127,127,127,.35));border-radius:16px;background:transparent;overflow:hidden}" +
    ".ov-row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:10px 12px;cursor:pointer;min-height:44px}.ov-plan{flex:0 0 100%;min-width:0;margin-top:-2px}.ov-plan .plan-wrap{position:relative}.ov-plan .plan-bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--divider-color,#e0e0e0)}.ov-plan .plan-seg{height:100%;min-width:0}.ov-plan .plan-fut{opacity:.6}.ov-plan .plan-none{background:repeating-linear-gradient(45deg,rgba(127,127,127,.35) 0 4px,transparent 4px 8px)}.ov-plan .plan-now{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;border-radius:1px;background:var(--primary-text-color,#000)}.ov-plan .plan-scale{position:relative;height:1.1em;margin-top:2px;font-size:11px;color:var(--secondary-text-color,#727272)}.ov-plan .plan-scale span{position:absolute;transform:translateX(-50%)}.ov-room+.ov-room{border-top:1px solid var(--divider-color,rgba(127,127,127,.25))}" +
    ".ov-chev{flex:none;color:var(--secondary-text-color,#727272);transition:transform .15s ease;--mdc-icon-size:22px}.ov-room.open .ov-chev{transform:rotate(90deg)}" +
    ".ov-body{display:none;padding:0 4px 8px}.ov-room.open .ov-body{display:block}" +
    ".ov-ico{width:36px;height:36px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;background:rgba(127,127,127,.18);color:var(--c);--mdc-icon-size:20px}" +
    ".ov-t{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}.ov-n{font-size:15px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ov-s{font-size:12px;color:var(--secondary-text-color,#727272);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".ov-r{flex:none;display:flex;flex-direction:column;align-items:flex-end;gap:2px;max-width:55%}.ov-vals{font-size:13px;white-space:nowrap}" +
    ".ov-devs{display:flex;gap:4px;--mdc-icon-size:18px}.ov-dev{display:inline-flex}" +
    ".ov-foot{margin:12px 4px 0;font-size:12px;color:var(--secondary-text-color,#727272);text-align:center}" +
    "@media (min-width:451px) and (min-height:501px){.sc-room-dialog{align-items:center;padding:24px}.sc-room-panel{max-width:560px;height:auto;max-height:calc(100% - 48px);border-radius:28px;border-bottom:1px solid var(--divider-color,rgba(127,127,127,.45));box-shadow:0 12px 48px rgba(0,0,0,.5);animation:sc-fade .18s ease-out}.sc-room-grip{display:none}.sc-room-bar{padding-top:10px}.sc-room-scroll{padding-bottom:0}}" +
    "</style>";
  const panel = document.createElement("div");
  panel.className = "sc-room-panel";
  const close = document.createElement("button");
  close.className = "sc-room-close";
  close.type = "button";
  close.setAttribute("aria-label", "Schließen");
  close.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>';
  const bar = document.createElement("div");
  bar.className = "sc-room-bar";
  const std = document.createElement("button");
  std.className = "sc-room-std";
  std.type = "button";
  std.innerHTML = '<ha-icon icon="mdi:window-shutter"></ha-icon>';
  std.setAttribute("aria-label", "Rollladen");
  std.title = "Rollladen";
  const titleEl = document.createElement("div");
  titleEl.className = "sc-room-title";
  close.setAttribute("aria-label", "Schließen");
  const listBtn = document.createElement("button");
  listBtn.className = "sc-room-list";
  listBtn.type = "button";
  listBtn.setAttribute("aria-label", "Übersicht");
  listBtn.title = "Übersicht";
  listBtn.innerHTML = '<ha-icon icon="mdi:floor-plan"></ha-icon>';
  const bell = document.createElement("button");
  bell.className = "sc-room-bell";
  bell.type = "button";
  bell.setAttribute("aria-label", "Benachrichtigungen");
  bell.setAttribute("aria-haspopup", "true");
  bell.title = "Benachrichtigungen";
  bell.innerHTML = '<ha-icon icon="mdi:bell-outline"></ha-icon>';
  const menuEl = document.createElement("div");
  menuEl.className = "sc-room-menu";
  menuEl.setAttribute("role", "menu");
  bar.appendChild(close);
  bar.appendChild(titleEl);
  const shutterId = (() => {
    if (overviewMode) return null;
    const eid = scFindRoomEntity(hass, key);
    const e = eid && hass.states[eid] && hass.states[eid].attributes.entitaeten;
    return e && e.rollladen ? e.rollladen : null;
  })();
  if (!overviewMode) {
    if (shutterId) bar.appendChild(std);
    bar.appendChild(listBtn);
    bar.appendChild(bell);
  }
  const grip = document.createElement("div");
  grip.className = "sc-room-grip";
  panel.appendChild(grip);
  panel.appendChild(bar);
  panel.appendChild(menuEl);
  const scroll = document.createElement("div");
  scroll.className = "sc-room-scroll";
  panel.appendChild(scroll);

  const entityId = overviewMode ? null : scFindRoomEntity(hass, key);
  let card = null;
  // Thermostat der Heizung liegt im Abschnitt "Raumklima" der Karte; die Karte
  // setzt dieses dauerhafte Element nach jedem Neuzeichnen in ihren Platzhalter.
  const thermo = document.createElement("div");
  thermo.className = "sc-room-thermo";
  const heatingId = entityId && hass.states[entityId] && hass.states[entityId].attributes.entitaeten
    ? hass.states[entityId].attributes.entitaeten.heizung
    : null;
  const hasHeating = !!(heatingId && hass.states[heatingId]);
  let headerSig = "";
  const syncHeader = () => {
    const h = card && card._compactHeader;
    const sig = h ? JSON.stringify(h) : "";
    if (sig === headerSig) return;
    headerSig = sig;
    syncMenu();
    titleEl.innerHTML = h
      ? `<div class="sc-room-sub" style="--c:${h.color}"><i></i><b>${esc(h.label)}</b></div><h1>${esc(h.name)}</h1>`
      : "";
  };
  let notifySig = null;
  const closeMenu = () => {
    menuEl.classList.remove("open");
    bell.classList.remove("open");
    bell.setAttribute("aria-expanded", "false");
  };
  const syncMenu = () => {
    const html = card && typeof card._compactNotify === "string" ? card._compactNotify : null;
    if (html === notifySig) return;
    notifySig = html;
    bell.style.display = html === null ? "none" : "";
    menuEl.innerHTML = html === null ? "" : html;
    if (html === null) closeMenu();
  };
  // Übersicht: Räume als aufklappbare Abschnitte (immer nur einer offen). Die
  // Zeilen werden einzeln aktualisiert, damit ein aufgeklappter Raum samt
  // Thermostat beim Neuzeichnen nicht zerstört wird.
  let ovHead = null;
  let ovList = null;
  let ovFoot = null;
  let ovOpen = null;
  const ovWraps = new Map();
  let ovCountTxt = "";
  const closeOv = () => {
    if (!ovOpen) return;
    if (ovOpen.thermoCtl) ovOpen.thermoCtl.stop();
    ovOpen.wrap.classList.remove("open");
    const rowEl = ovOpen.wrap.querySelector(".ov-row");
    if (rowEl) rowEl.setAttribute("aria-expanded", "false");
    ovOpen.body.innerHTML = "";
    ovOpen = null;
  };
  const openOv = (id) => {
    const wrap = ovWraps.get(id);
    if (!wrap) return;
    closeOv();
    const h = root.hass;
    const body = wrap.querySelector(".ov-body");
    const c = document.createElement("smart-climate-card");
    c.setConfig({ entities: [id], compact_room: true });
    c._headerSink = true;
    const st = h && h.states[id];
    const hid = st && st.attributes.entitaeten ? st.attributes.entitaeten.heizung : null;
    let ctl = null;
    if (hid && h.states[hid]) {
      const th = document.createElement("div");
      th.className = "sc-room-thermo";
      c._thermoEl = th;
      ctl = scBuildThermostat(th, hid, root);
    }
    c.hass = h;
    body.appendChild(c);
    wrap.classList.add("open");
    const rowEl = wrap.querySelector(".ov-row");
    if (rowEl) rowEl.setAttribute("aria-expanded", "true");
    ovOpen = { id, wrap, body, card: c, thermoCtl: ctl };
    requestAnimationFrame(() => {
      scroll.scrollTop += wrap.getBoundingClientRect().top - scroll.getBoundingClientRect().top - 8;
    });
  };
  const renderOverview = (h) => {
    const o = scOverview(h);
    if (!ovHead) {
      scroll.innerHTML = '<div class="ov"><div class="ov-headbox"></div><div class="ov-sec">Räume</div><div class="ov-list"></div><div class="ov-footbox"></div></div>';
      ovHead = scroll.querySelector(".ov-headbox");
      ovList = scroll.querySelector(".ov-list");
      ovFoot = scroll.querySelector(".ov-footbox");
    }
    if (ovHead._sig !== o.head) { ovHead._sig = o.head; ovHead.innerHTML = o.head || ""; }
    if (ovFoot._sig !== o.foot) { ovFoot._sig = o.foot; ovFoot.innerHTML = o.foot || ""; }
    const txt = `<div class="sc-room-sub"><b style="color:inherit;font-weight:400">${o.count} ${o.count === 1 ? "Raum" : "Räume"}</b></div><h1>Übersicht</h1>`;
    if (txt !== ovCountTxt) { ovCountTxt = txt; titleEl.innerHTML = txt; }
    const want = o.rooms.map((r) => r.id);
    for (const [id, w] of [...ovWraps]) {
      if (!want.includes(id)) {
        if (ovOpen && ovOpen.id === id) closeOv();
        w.remove();
        ovWraps.delete(id);
      }
    }
    o.rooms.forEach((r, i) => {
      let w = ovWraps.get(r.id);
      if (!w) {
        w = document.createElement("div");
        w.className = "ov-room";
        w.dataset.roomId = r.id;
        w.innerHTML = '<div class="ov-row" role="button" tabindex="0" aria-expanded="false"></div><div class="ov-body"></div>';
        ovWraps.set(r.id, w);
      }
      if (w._sig !== r.html) { w._sig = r.html; w.querySelector(".ov-row").innerHTML = r.html; }
      if (ovList.children[i] !== w) ovList.insertBefore(w, ovList.children[i] || null);
    });
  };
  if (overviewMode) {
    renderOverview(hass);
  } else if (entityId) {
    card = document.createElement("smart-climate-card");
    card.setConfig({ entities: [entityId], compact_room: true });
    card._headerSink = true;
    card._notifyMenu = true;
    if (hasHeating) card._thermoEl = thermo;
    card.hass = hass;
    scroll.appendChild(card);
    syncHeader();
  } else {
    const missing = document.createElement("div");
    missing.className = "sc-room-missing";
    missing.textContent = `Raum nicht gefunden: ${key}`;
    scroll.appendChild(missing);
  }
  overlay.appendChild(panel);

  // Thermostat der Heizung: eigene Bedienelemente (siehe scBuildThermostat).
  let thermoCtl = null;
  if (hasHeating) {
    thermoCtl = scBuildThermostat(thermo, heatingId, root);
  }

  // In <body> einhängen: <home-assistant> hat ein eigenes Shadow-DOM ohne
  // Platz für Kinder, ein dort angehängter Dialog würde nie gezeichnet.
  document.body.appendChild(overlay);
  // Damit erreicht hass-more-info (Tippen auf eine Bezeichnung) die
  // Dialogverwaltung von Home Assistant nicht mehr von selbst: Ereignis auf
  // <home-assistant> weiterleiten und den Raum-Dialog dabei schließen.
  overlay.addEventListener("hass-more-info", (ev) => {
    ev.stopPropagation();
    const detail = Object.assign({}, ev.detail, { scBypass: true });
    scCloseRoomDialog();
    root.dispatchEvent(
      new CustomEvent("hass-more-info", { detail, bubbles: true, composed: true })
    );
  });

  const onKey = (ev) => {
    if (ev.key !== "Escape") return;
    // Esc schließt zuerst das offene Menü, danach das Popup.
    if (menuEl.classList.contains("open")) { closeMenu(); ev.stopPropagation(); return; }
    scCloseRoomDialog();
  };
  document.addEventListener("keydown", onKey, true);
  close.addEventListener("click", scCloseRoomDialog);
  bell.addEventListener("click", (ev) => {
    ev.stopPropagation();
    if (menuEl.classList.contains("open")) { closeMenu(); return; }
    menuEl.style.setProperty("--mt", `${bar.offsetTop + bar.offsetHeight}px`);
    menuEl.classList.add("open");
    bell.classList.add("open");
    bell.setAttribute("aria-expanded", "true");
  });
  // Tipp außerhalb des Menüs schließt es (ein Tipp auf einen Eintrag im Menü
  // öffnet die Standardansicht und schließt dabei das ganze Popup).
  panel.addEventListener("click", (ev) => {
    if (!menuEl.classList.contains("open")) return;
    const path = ev.composedPath();
    if (path.includes(menuEl) || path.includes(bell)) return;
    closeMenu();
  });
  menuEl.addEventListener("click", (ev) => {
    const t = ev.target && ev.target.closest ? ev.target.closest("[data-entity]") : null;
    if (!t) return;
    t.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId: t.dataset.entity } }));
  });
  listBtn.addEventListener("click", () => openRoomDialog(SC_OVERVIEW_KEY));
  const toggleRow = (ev) => {
    const rowEl = ev.target && ev.target.closest ? ev.target.closest(".ov-row") : null;
    if (!rowEl) return;
    const wrap = rowEl.closest(".ov-room");
    if (!wrap) return;
    if (ovOpen && ovOpen.id === wrap.dataset.roomId) closeOv();
    else openOv(wrap.dataset.roomId);
  };
  scroll.addEventListener("click", (ev) => { if (overviewMode) toggleRow(ev); });
  scroll.addEventListener("keydown", (ev) => {
    if (overviewMode && (ev.key === "Enter" || ev.key === " ") && ev.target && ev.target.classList && ev.target.classList.contains("ov-row")) {
      ev.preventDefault();
      toggleRow(ev);
    }
  });
  std.addEventListener("click", () => {
    scCloseRoomDialog();
    if (shutterId) {
      root.dispatchEvent(
        new CustomEvent("hass-more-info", {
          detail: { entityId: shutterId, scBypass: true },
          bubbles: true,
          composed: true,
        })
      );
    }
  });
  overlay.addEventListener("click", (ev) => {
    if (ev.target === overlay) scCloseRoomDialog();
  });
  // Wegwischen nach unten wie bei den Home-Assistant-Fenstern: am Kopfbereich
  // immer, im Inhalt nur, wenn er ganz oben steht. Über 110 px oder schnell
  // schließt es, sonst federt es zurück.
  let sw = null;
  const isSheet = () => !(window.matchMedia && window.matchMedia("(min-width:451px) and (min-height:501px)").matches);
  panel.addEventListener("touchstart", (ev) => {
    if (ev.touches.length !== 1 || !isSheet() || ev.composedPath().includes(menuEl)) { sw = null; return; }
    const inBar = ev.composedPath().includes(bar) || ev.composedPath().includes(grip);
    sw = { y: ev.touches[0].clientY, t: Date.now(), ok: inBar || scroll.scrollTop <= 0, drag: false, dy: 0 };
  }, { passive: true });
  panel.addEventListener("touchmove", (ev) => {
    if (!sw || !sw.ok || !ev.touches.length) return;
    const dy = ev.touches[0].clientY - sw.y;
    if (!sw.drag && dy > 8) {
      sw.drag = true;
      panel.style.animation = "none";
      panel.style.transition = "none";
    }
    if (!sw.drag) return;
    sw.dy = Math.max(0, dy);
    panel.style.transform = `translateY(${sw.dy}px)`;
  }, { passive: true });
  const swipeEnd = () => {
    if (!sw || !sw.drag) { sw = null; return; }
    const dt = Math.max(1, Date.now() - sw.t);
    const fast = sw.dy > 40 && sw.dy / dt > 0.5;
    const go = sw.dy > 110 || fast;
    sw = null;
    panel.style.transition = "transform .2s ease-out";
    if (go) {
      panel.style.transform = "translateY(100%)";
      setTimeout(scCloseRoomDialog, 190);
    } else {
      panel.style.transform = "";
    }
  };
  panel.addEventListener("touchend", swipeEnd, { passive: true });
  panel.addEventListener("touchcancel", swipeEnd, { passive: true });
  // Bei offenem Dialog neue Zustände übernehmen (die Karte selbst bekommt
  // hass sonst nur vom Dashboard).
  const timer = setInterval(() => {
    const current = root.hass;
    if (overviewMode && current) {
      renderOverview(current);
      if (ovOpen) {
        if (current !== ovOpen.card._hass) ovOpen.card.hass = current;
        if (ovOpen.thermoCtl) ovOpen.thermoCtl.update(current);
      }
    }
    if (card && current && current !== card._hass) card.hass = current;
    if (thermoCtl && current) thermoCtl.update(current);
    syncHeader();
  }, 2000);
  // Seite dahinter sperren, solange der Dialog offen ist: nur über die Abfänger für
  // wheel/touch (unten), nicht über overflow auf html/body - das setzte in der iOS-App
  // die Scrollposition des Dashboards zurück (Lektion 161).
  const pageScroll = { x: window.scrollX, y: window.scrollY };

  // Seite dahinter sperren: Mausrad und Wischgesten auf Dokumentebene
  // abfangen. Home Assistant scrollt in einem eigenen inneren Container, den
  // overflow auf html/body nicht erreicht. Erlaubt ist nur das Scrollen im
  // Inhalt des Dialogs, solange dort noch etwas zu scrollen ist.
  const canScroll = (dy) => {
    if (scroll.scrollHeight <= scroll.clientHeight + 1) return false;
    if (dy > 0) return scroll.scrollTop > 0;
    if (dy < 0) return scroll.scrollTop + scroll.clientHeight < scroll.scrollHeight - 1;
    return false;
  };
  const inScroll = (ev) => ev.composedPath().includes(scroll);
  const onWheel = (ev) => {
    if (!(inScroll(ev) && canScroll(-ev.deltaY)) && ev.cancelable) ev.preventDefault();
  };
  let lockY = null;
  const onLockStart = (ev) => {
    lockY = ev.touches.length ? ev.touches[0].clientY : null;
  };
  const onLockMove = (ev) => {
    if (!ev.touches.length || lockY === null) return;
    const y = ev.touches[0].clientY;
    const dy = y - lockY;
    lockY = y;
    if (inScroll(ev) && canScroll(dy)) return;
    if (ev.cancelable) ev.preventDefault();
  };
  document.addEventListener("wheel", onWheel, { capture: true, passive: false });
  document.addEventListener("touchstart", onLockStart, { capture: true, passive: true });
  document.addEventListener("touchmove", onLockMove, { capture: true, passive: false });
  scRoomDialog = { overlay, thermo, thermoCtl, cleanup: closeOv, timer, onKey, onWheel, onLockStart, onLockMove, pageScroll };
}

if (!window.__smartClimateRoomDialog) {
  window.__smartClimateRoomDialog = true;
  window.addEventListener("hass-more-info", scInterceptMoreInfo, true);
  window.addEventListener("ll-custom", (ev) => {
    const detail = ev && ev.detail;
    if (detail && detail.smart_climate_overview) openRoomDialog(SC_OVERVIEW_KEY);
    else if (detail && detail.smart_climate_room) openRoomDialog(detail.smart_climate_room);
  });
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "smart-climate-card")) {
  window.customCards.push({
    type: "smart-climate-card",
    name: "Smart Climate Karte",
    description: "Lüftungsübersicht für Smart Climate.",
  });
}
