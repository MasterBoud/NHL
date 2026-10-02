const $ = (sel) => document.querySelector(sel);
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};
const state = { date: null, team: store.get("team") || "", timer: null };

const api = async (path) => {
  const res = await fetch(path);
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || res.statusText);
  return body;
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

const startTime = (utc) =>
  utc ? new Date(utc).toLocaleTimeString("fr-CA", { hour: "2-digit", minute: "2-digit" }) : "";

function statusLine(g) {
  if (g.status === "live") {
    const clock = g.intermission ? "Entracte" : g.clock;
    return `<span class="badge">EN DIRECT</span> ${esc(g.period)} · ${esc(clock)}`;
  }
  if (g.status === "final") {
    const extra = g.period_type === "OT" ? " (Prol.)" : g.period_type === "SO" ? " (TB)" : "";
    return `Final${extra}`;
  }
  if (g.status === "pregame") return `Avant-match · ${startTime(g.start_time_utc)}`;
  return startTime(g.start_time_utc);
}

function teamRow(t, other, g) {
  const showScore = g.status !== "scheduled" && g.status !== "pregame";
  const loser = g.status === "final" && t.score < other.score;
  return `<div class="row${loser ? " loser" : ""}">
    <img src="${esc(t.logo)}" alt="" loading="lazy">
    <span class="name">${esc(t.name || t.abbrev)}</span>
    ${showScore ? `<span class="score">${t.score ?? 0}</span>` : ""}
  </div>`;
}

function gameCard(g) {
  const sog = g.away.sog != null ? `Tirs ${g.away.sog}–${g.home.sog}` : esc(g.venue);
  return `<article class="game ${g.status}" data-id="${g.id}">
    ${teamRow(g.away, g.home, g)}
    ${teamRow(g.home, g.away, g)}
    <div class="meta"><span>${statusLine(g)}</span><span>${sog}</span></div>
  </article>`;
}

async function loadScores() {
  clearTimeout(state.timer);
  const params = new URLSearchParams();
  if (state.date) params.set("date", state.date);
  if (state.team) params.set("team", state.team);
  try {
    const board = await api(`/api/scores?${params}`);
    state.date = board.date;
    state.prev = board.prev_date;
    state.next = board.next_date;
    $("#date").value = board.date || "";
    $("#games").innerHTML = board.games.map(gameCard).join("");
    $("#status").textContent = board.games.length
      ? `${board.games.length} match(s)` + (board.has_live ? " · mise à jour auto toutes les 15 s" : "")
      : "Aucun match pour cette date.";
    if (board.has_live) state.timer = setTimeout(loadScores, 15000);
  } catch (err) {
    $("#status").textContent = `Erreur : ${err.message}`;
  }
}

async function showGame(id) {
  const g = await api(`/api/games/${id}`);
  const goals = g.goals.length
    ? g.goals.map((b) => `<div class="goal"><strong>${esc(b.team)}</strong> ${b.away_score}-${b.home_score}
        · P${b.period} ${esc(b.time)} — ${esc(b.scorer)} (${b.scorer_total ?? "?"})
        ${b.strength !== "EV" ? `<span class="badge">${esc(b.strength)}</span>` : ""}
        <div class="muted">${b.assists.map((a) => `${esc(a.name)} (${a.total ?? "?"})`).join(", ") || "Sans aide"}</div></div>`).join("")
    : `<p class="muted">Aucun but.</p>`;
  $("#detail-body").innerHTML = `<h2>${esc(g.away.abbrev)} ${g.away.score ?? ""} @ ${esc(g.home.abbrev)} ${g.home.score ?? ""}</h2>
    <p class="muted">${statusLine(g)} · ${esc(g.venue)}</p>${goals}`;
  $("#detail").showModal();
}

async function loadStandings() {
  const { standings } = await api("/api/standings");
  $("#standings tbody").innerHTML = standings.map((r, i) => `<tr>
    <td>${i + 1}</td><td><img src="${esc(r.logo)}" alt="">${esc(r.name)}</td>
    <td>${r.games_played}</td><td>${r.wins}</td><td>${r.losses}</td><td>${r.ot_losses}</td>
    <td><strong>${r.points}</strong></td><td>${r.goal_diff > 0 ? "+" : ""}${r.goal_diff}</td><td>${esc(r.streak)}</td>
  </tr>`).join("");
}

$("#prev").onclick = () => { if (state.prev) { state.date = state.prev; loadScores(); } };
$("#next").onclick = () => { if (state.next) { state.date = state.next; loadScores(); } };
$("#today").onclick = () => { state.date = null; loadScores(); };
$("#date").onchange = (e) => { state.date = e.target.value || null; loadScores(); };
$("#team").value = state.team;
$("#team").oninput = (e) => {
  const v = e.target.value.trim().toUpperCase();
  if (v.length === 0 || v.length === 3) {
    state.team = v;
    store.set("team", v);
    loadScores();
  }
};
$("#games").onclick = (e) => {
  const card = e.target.closest(".game");
  if (card) showGame(card.dataset.id).catch((err) => alert(err.message));
};
document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b === btn));
    const view = btn.dataset.view;
    $("#scores-view").hidden = view !== "scores";
    $("#standings-view").hidden = view !== "standings";
    if (view === "standings") loadStandings().catch((err) => alert(err.message));
  };
});

loadScores();
