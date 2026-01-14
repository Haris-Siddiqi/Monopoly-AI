const playerColors = ["#f94144", "#277da1", "#f8961e", "#90be6d"];

const startScreen = document.getElementById("start-screen");
const gameScreen = document.getElementById("game-screen");
const startForm = document.getElementById("start-form");
const boardEl = document.getElementById("board");
const playersEl = document.getElementById("players");
const eventLogEl = document.getElementById("event-log");
const statusEl = document.getElementById("status");
const turnIndicator = document.getElementById("turn-indicator");

const rollBtn = document.getElementById("roll-btn");
const jailRollBtn = document.getElementById("jail-roll-btn");
const jailPayBtn = document.getElementById("jail-pay-btn");
const buyBtn = document.getElementById("buy-btn");
const declineBtn = document.getElementById("decline-btn");
const endTurnBtn = document.getElementById("end-turn-btn");

let lastState = null;
let polling = null;

startForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const names = Array.from(startForm.querySelectorAll("input[name='player']"))
    .map((input) => input.value.trim())
    .filter((name) => name.length > 0);
  if (names.length < 2 || names.length > 4) {
    setStatus("Enter 2-4 player names.");
    return;
  }
  await apiPost("/api/start", { players: names });
  startScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
  await refreshState();
  if (!polling) {
    polling = setInterval(refreshState, 700);
  }
});

rollBtn.addEventListener("click", () => action("/api/roll"));
jailRollBtn.addEventListener("click", () => action("/api/jail/roll"));
jailPayBtn.addEventListener("click", () => action("/api/jail/pay"));
buyBtn.addEventListener("click", () => action("/api/buy"));
declineBtn.addEventListener("click", () => action("/api/decline"));
endTurnBtn.addEventListener("click", () => action("/api/end_turn"));

async function action(url) {
  const result = await apiPost(url, {});
  if (result && result.error) {
    setStatus(result.error);
  }
  await refreshState();
}

async function refreshState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  if (!data.started) {
    return;
  }
  lastState = data;
  renderBoard(data);
  renderPlayers(data);
  renderEvents(data);
  renderControls(data);
}

function renderBoard(state) {
  boardEl.innerHTML = "";
  const spaces = state.board;
  spaces.forEach((space, index) => {
    const cell = document.createElement("div");
    cell.className = "space";
    const { row, col } = mapIndexToGrid(index);
    cell.style.gridRow = row;
    cell.style.gridColumn = col;

    const name = document.createElement("div");
    name.className = "space-name";
    name.textContent = space.name;
    cell.appendChild(name);

    const tokens = document.createElement("div");
    tokens.className = "token-row";
    state.players.forEach((player, idx) => {
      if (player.position === index && !player.bankrupt) {
        const token = document.createElement("span");
        token.className = "token";
        token.style.background = playerColors[idx];
        token.title = player.name;
        tokens.appendChild(token);
      }
    });
    cell.appendChild(tokens);

    const propState = state.properties[String(space.property_id)];
    if (propState && propState.owner_id !== null) {
      const owner = document.createElement("div");
      owner.className = "owner";
      owner.textContent = `P${propState.owner_id + 1}`;
      cell.appendChild(owner);
    }

    boardEl.appendChild(cell);
  });
}

function renderPlayers(state) {
  playersEl.innerHTML = "";
  state.players.forEach((player, idx) => {
    const card = document.createElement("div");
    card.className = "player-card";
    card.innerHTML = `
      <strong style="color: ${playerColors[idx]}">${player.name}</strong><br>
      Cash: $${player.cash}<br>
      Position: ${player.position}<br>
      ${player.in_jail ? "In Jail" : ""}
    `;
    playersEl.appendChild(card);
  });
}

function renderEvents(state) {
  eventLogEl.innerHTML = "";
  state.event_log.forEach((event) => {
    const li = document.createElement("li");
    li.textContent = event;
    eventLogEl.appendChild(li);
  });
}

function renderControls(state) {
  const phase = state.turn_phase;
  const currentPlayer = state.players[state.current_player];
  turnIndicator.textContent = `Current: ${currentPlayer.name}`;

  rollBtn.disabled = phase !== "await_roll";
  jailRollBtn.disabled = phase !== "await_jail_action";
  jailPayBtn.disabled = phase !== "await_jail_action";
  buyBtn.disabled = phase !== "await_buy_decision";
  declineBtn.disabled = phase !== "await_buy_decision";
  endTurnBtn.disabled = phase !== "turn_over";

  if (phase === "await_buy_decision" && state.pending_property_id !== null) {
    const prop = state.properties[String(state.pending_property_id)];
    setStatus(`Buy ${prop.name}?`);
  } else if (phase === "await_roll") {
    setStatus("Roll the dice.");
  } else if (phase === "turn_over") {
    setStatus("End the turn or roll again if doubles.");
  }
}

function mapIndexToGrid(index) {
  if (index <= 10) {
    return { row: 11, col: 11 - index };
  }
  if (index <= 19) {
    return { row: 11 - (index - 10), col: 1 };
  }
  if (index <= 30) {
    return { row: 1, col: 1 + (index - 20) };
  }
  return { row: 1 + (index - 30), col: 11 };
}

async function apiPost(url, body) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    if (!response.ok) {
      const error = await response.json();
      return { error: error.detail || "Request failed" };
    }
    return await response.json();
  } catch (err) {
    return { error: "Network error" };
  }
}

function setStatus(message) {
  statusEl.textContent = message;
}
