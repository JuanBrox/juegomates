import random
import threading
import time
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="El Reino Mágico de los Puntos", page_icon="🦄", layout="wide")

TITULO = "🦄 El Reino Mágico de los Puntos 🧚"
START_POINTS = 100
COLS = 6
MAX_PLAYERS = 4
TOKENS = ["🦄", "🧚", "🦋", "🌟"]

# (nombre, puntos, emoji)
SQUARES = [("Salida", 0, "🏰")] + [
    ("Sonrío", 30, "😊"),
    ("Duermo poco", -10, "😴"),
    ("Comparto mi merienda", 20, "🍪"),
    ("Grito", -40, "😤"),
    ("Hago los deberes", 50, "📚"),
    ("Obedezco", 70, "🦄"),
    ("Como mal", -20, "🍔"),
    ("Ayudo a un amigo", 30, "🤝"),
    ("Digo gracias", 10, "🙏"),
    ("Me quejo", -50, "😩"),
    ("Recojo mi cuarto", 40, "🧸"),
    ("Leo un cuento", 40, "📖"),
    ("Dejo juguetes tirados", -30, "🧩"),
    ("Perdono a un amigo", 60, "💖"),
    ("Doy un abrazo", 20, "🤗"),
    ("Digo una mentira", -60, "🤥"),
    ("Cuido las plantas", 20, "🌸"),
    ("No comparto", -30, "🙅"),
    ("Ayudo en casa", 50, "🧹"),
    ("Me enfado y no escucho", -40, "👂"),
    ("Digo la verdad", 60, "⭐"),
    ("Me lavo los dientes", 10, "🪥"),
] + [("Meta", 0, "🌈")]
LAST = len(SQUARES) - 1

RULES = [
    "Juegan de 1 a 4 jugadores. Cada uno elige una ficha (🦄 🧚 🦋 🌟) y empieza en la Salida con 100 puntos.",
    "Por turnos, tira el dado y avanza tantas casillas como indique.",
    "Lee la casilla donde caes: si el número es positivo (+) se suma; si es negativo (−) se resta.",
    "La suma o la resta se hace mentalmente. Después se anota en la hoja de puntos.",
    "Los puntos nunca bajan de 0.",
    "Quien llega a la Meta 🌈 se queda allí y espera a los demás (no hace falta tirada exacta).",
    "Cuando todos han llegado a la Meta, gana quien tiene más puntos. Si hay empate, comparten la corona. 👑",
    "Online: uno crea la sala y comparte el código de 4 letras; los demás entran con ese código desde su dispositivo.",
]

FUENTES = (
    "Fuentes: libro de Matemáticas de 3.º de Primaria, página 43 (ejemplos de casillas), "
    "y las ideas de la clase sobre buenas acciones. Añade aquí las fuentes que hayas usado."
)

CSS = """
<style>
.board{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;max-width:900px;margin:auto}
.cell{position:relative;border-radius:14px;padding:6px 4px;text-align:center;min-height:96px;display:flex;
flex-direction:column;justify-content:center;align-items:center;font-family:'Comic Sans MS',cursive,sans-serif;
border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.18)}
.cell .n{position:absolute;top:4px;left:4px;width:28px;height:28px;border-radius:50%;background:#9b4dca;
color:#fff;font-size:15px;font-weight:bold;display:flex;align-items:center;justify-content:center;
box-shadow:0 1px 3px rgba(0,0,0,.3)}
.cell .arr{position:absolute;bottom:3px;right:5px;font-size:14px}
.cell .e{font-size:26px}
.cell .t{font-size:12px;line-height:1.1;color:#333;font-weight:bold}
.cell .p{font-size:20px;font-weight:bold}
.pos{background:linear-gradient(135deg,#d9f7e8,#b9ecd6)} .pos .p{color:#0a8a55}
.neg{background:linear-gradient(135deg,#ffe0e8,#ffc2d4)} .neg .p{color:#c0173f}
.special{background:linear-gradient(135deg,#efe0ff,#d5c0ff)} .special .p{color:#6a2fc0}
.tok{font-size:22px}
.titulo{text-align:center;font-size:34px;font-weight:bold;color:#9b4dca;font-family:'Comic Sans MS',cursive,sans-serif}
.die{width:110px;height:110px;margin:auto;background:#fff;border-radius:20px;border:4px solid #9b4dca;
box-shadow:0 4px 10px rgba(0,0,0,.25);display:grid;grid-template-columns:repeat(3,1fr);
grid-template-rows:repeat(3,1fr);padding:12px}
.die i{display:block;width:22px;height:22px;border-radius:50%;place-self:center}
.die i.pip{background:radial-gradient(circle at 30% 30%,#d9a8ff,#9b4dca)}
.die .q{grid-column:1/4;grid-row:1/4;place-self:center;font-size:56px;color:#9b4dca;font-weight:bold}
.die.rolling{transform:rotate(12deg)}
.scores{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:8px 0 14px}
.score{background:#fff;border:3px solid #d5c0ff;border-radius:16px;padding:8px 16px;min-width:150px;text-align:center;
font-family:'Comic Sans MS',cursive,sans-serif;color:#333}
.score b{display:block;font-size:32px;color:#9b4dca}
.score small{color:#777}
.score.turno{border-color:#ffb703;box-shadow:0 0 12px #ffd166}
.codigo{text-align:center;font-size:44px;letter-spacing:10px;font-weight:bold;color:#9b4dca;
font-family:'Comic Sans MS',cursive,sans-serif}
@media(max-width:600px){.cell{min-height:70px}.cell .t{font-size:9px}.cell .e{font-size:18px}.cell .p{font-size:14px}
.cell .n{width:22px;height:22px;font-size:12px}}
</style>
"""

# ---------------------------------------------------------------------------
# Almacén compartido entre todos los dispositivos (vive mientras la app esté encendida)
# ---------------------------------------------------------------------------


@st.cache_resource
def get_store():
    return {"rooms": {}, "hall": [], "lock": threading.RLock()}


STORE = get_store()
LOCK = STORE["lock"]


def fmt(p):
    return f"{p:+d}".replace("-", "−") if p else ""


def board_html(players=None):
    players = players or []
    cells = []
    for i, (name, pts, emoji) in enumerate(SQUARES):
        r = i // COLS
        c = i % COLS if r % 2 == 0 else COLS - 1 - i % COLS
        cls = "pos" if pts > 0 else "neg" if pts < 0 else "special"
        if i == LAST:
            arr = ""
        elif i % COLS == COLS - 1:
            arr = "⬇️"
        else:
            arr = "➡️" if r % 2 == 0 else "⬅️"
        toks = "".join(p["token"] for p in players if p["pos"] == i)
        cells.append(
            f'<div class="cell {cls}" style="grid-row:{r + 1};grid-column:{c + 1}">'
            f'<span class="n">{i}</span><span class="arr">{arr}</span><span class="e">{emoji}</span>'
            f'<span class="t">{name}</span><span class="p">{fmt(pts)}</span>'
            f'<span class="tok">{toks}</span></div>'
        )
    return '<div class="board">' + "".join(cells) + "</div>"


PIPS = {1: [5], 2: [1, 9], 3: [1, 5, 9], 4: [1, 3, 7, 9], 5: [1, 3, 5, 7, 9], 6: [1, 3, 4, 6, 7, 9]}


def die_html(value=None, rolling=False):
    if value is None:
        inner = '<span class="q">?</span>'
    else:
        inner = "".join('<i class="pip"></i>' if k in PIPS[value] else "<i></i>" for k in range(1, 10))
    return f'<div class="die{" rolling" if rolling else ""}">{inner}</div>'


def scoreboard_html(room):
    ranking = sorted(room["players"], key=lambda p: -p["score"])
    medals = ["🥇", "🥈", "🥉", "🎀"]
    cur = None if room["finished"] else room["players"][room["turn"]]
    cards = []
    for i, p in enumerate(ranking):
        turno = " turno" if p is cur else ""
        estado = "🌈 en la meta" if p["done"] else f"casilla {p['pos']}"
        cards.append(
            f'<div class="score{turno}"><span>{medals[i]} {p["token"]} {p["name"]}</span>'
            f'<b>{p["score"]}</b><small>{estado}</small></div>'
        )
    return '<div class="scores">' + "".join(cards) + "</div>"


def printable_html():
    return (
        "<html><head><meta charset='utf-8'><title>Tablero</title>" + CSS + "</head><body>"
        f"<div class='titulo'>{TITULO}</div><br>" + board_html() +
        f"<p style='text-align:center;font-family:sans-serif'>{FUENTES}</p>"
        "<h3 style='font-family:sans-serif'>Normas</h3><ol style='font-family:sans-serif'>"
        + "".join(f"<li>{r}</li>" for r in RULES) + "</ol></body></html>"
    )


# ---------------------------------------------------------------------------
# Lógica de salas y partida
# ---------------------------------------------------------------------------


def new_code():
    while True:
        code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=4))
        if code not in STORE["rooms"]:
            return code


def add_player(room, name, owner):
    p = {"name": name, "token": TOKENS[len(room["players"])], "pos": 0,
         "score": START_POINTS, "done": False, "owner": owner}
    room["players"].append(p)
    return p


def create_room(names, local, owner):
    with LOCK:
        now = time.time()
        for c in [c for c, r in STORE["rooms"].items() if now - r["created"] > 6 * 3600]:
            del STORE["rooms"][c]
        code = new_code()
        room = {"code": code, "local": local, "started": local, "players": [], "turn": 0,
                "pending": None, "log": [], "last_roll": None, "finished": False,
                "recorded": False, "created": now}
        for n in names:
            add_player(room, n, owner)
        STORE["rooms"][code] = room
        return code


def join_room(code, name, owner):
    with LOCK:
        room = STORE["rooms"].get(code)
        if not room:
            return False, "No encuentro esa sala. Revisa el código. 🔍"
        if room["local"]:
            return False, "Esa sala es de un solo dispositivo."
        for p in room["players"]:
            if p["name"].lower() == name.lower():
                p["owner"] = owner  # volver a entrar
                return True, None
        if room["started"]:
            return False, "La partida ya ha empezado."
        if len(room["players"]) >= MAX_PLAYERS:
            return False, "La sala está llena."
        add_player(room, name, owner)
        return True, None


def current(room):
    return room["players"][room["turn"]]


def record_result(room):
    if room["recorded"]:
        return
    room["recorded"] = True
    best = max(p["score"] for p in room["players"])
    winners = " y ".join(p["name"] for p in room["players"] if p["score"] == best)
    STORE["hall"].append({"Fecha": datetime.now().strftime("%d/%m"), "Ganador/a": winners,
                          "Puntos": best, "Jugadores": len(room["players"])})
    del STORE["hall"][:-50]


def next_turn(room):
    players = room["players"]
    if all(p["done"] for p in players):
        room["finished"] = True
        record_result(room)
        return
    for _ in range(len(players)):
        room["turn"] = (room["turn"] + 1) % len(players)
        if not players[room["turn"]]["done"]:
            return


def can_act(room, actor):
    return room["local"] or current(room)["owner"] == actor


def roll_action(code, actor):
    with LOCK:
        room = STORE["rooms"].get(code)
        if not room or room["finished"] or room["pending"] or not room["started"] or not can_act(room, actor):
            return
        p = current(room)
        room["last_roll"] = random.randint(1, 6)
        p["pos"] = min(p["pos"] + room["last_roll"], LAST)
        name, pts, emoji = SQUARES[p["pos"]]
        if p["pos"] == LAST:
            p["done"] = True
        if pts == 0:
            room["log"].append({"Jugador": p["name"], "Casilla": f"{emoji} {name}", "Puntos": 0, "Total": p["score"]})
            next_turn(room)
        else:
            room["pending"] = {"before": p["score"], "delta": pts, "sq": f"{emoji} {name}"}


def check_action(code, actor, answer):
    with LOCK:
        room = STORE["rooms"].get(code)
        if not room or not room["pending"] or not can_act(room, actor):
            return None
        pend = room["pending"]
        p = current(room)
        expected = max(0, pend["before"] + pend["delta"])
        if answer != expected:
            return False
        p["score"] = expected
        room["log"].append({"Jugador": p["name"], "Casilla": pend["sq"], "Puntos": pend["delta"], "Total": expected})
        room["pending"] = None
        next_turn(room)
        return True


def skip_action(code):
    with LOCK:
        room = STORE["rooms"].get(code)
        if room and not room["finished"]:
            room["pending"] = None
            next_turn(room)


# ---------------------------------------------------------------------------
# Pantallas
# ---------------------------------------------------------------------------


def refresh():
    """Recarga solo el fragmento; si no es posible, recarga la app entera."""
    try:
        st.rerun(scope="fragment")
    except st.errors.StreamlitAPIException:
        st.rerun()


def animate_die(placeholder):
    for _ in range(10):
        placeholder.markdown(die_html(random.randint(1, 6), True), unsafe_allow_html=True)
        time.sleep(0.08)


@st.fragment(run_every=3)
def game_view(code):
    pid = st.session_state.pid
    room = STORE["rooms"].get(code)
    if room is None:
        st.warning("La sala ya no existe (caducó o se reinició la app).")
        if st.button("Volver al inicio"):
            st.session_state.pop("room", None)
            st.rerun()
        return

    h1, h2 = st.columns([3, 1])
    h1.markdown(f"### 🏠 Sala **{code}** · {'un dispositivo' if room['local'] else 'online'}")
    if h2.button("🚪 Salir de la sala", key=f"leave_{code}"):
        st.session_state.pop("room", None)
        st.rerun()

    is_host = room["local"] or room["players"][0]["owner"] == pid

    if not room["started"]:
        st.markdown(f'<div class="codigo">{code}</div>', unsafe_allow_html=True)
        st.info(f"Comparte este código con quien quiera jugar (hasta {MAX_PLAYERS} jugadores).")
        for p in room["players"]:
            st.write(f"{p['token']} **{p['name']}**")
        if is_host:
            if st.button("▶️ ¡Empezar la partida!", type="primary", key=f"start_{code}"):
                with LOCK:
                    room["started"] = True
                refresh()
        else:
            st.caption("Esperando a que empiece quien creó la sala… ⏳")
        return

    st.markdown(scoreboard_html(room), unsafe_allow_html=True)
    st.markdown(board_html(room["players"]), unsafe_allow_html=True)

    if room["finished"]:
        if not st.session_state.get(f"balloons_{code}"):
            st.balloons()
            st.session_state[f"balloons_{code}"] = True
        best = max(p["score"] for p in room["players"])
        winners = " y ".join(p["name"] for p in room["players"] if p["score"] == best)
        st.success(f"👑 ¡Gana {winners} con {best} puntos! ¡Enhorabuena!")
    else:
        p = current(room)
        can = can_act(room, pid)
        pend = room["pending"]
        st.subheader(f"✨ ¡Te toca, {p['name']}!" if can and not room["local"] else f"Turno de {p['token']} {p['name']}")
        dcol, icol = st.columns([1, 2])
        die_ph = dcol.empty()
        die_ph.markdown(die_html(room["last_roll"]), unsafe_allow_html=True)
        with icol:
            if pend is None:
                if can:
                    if st.button("🎲 Tirar el dado", type="primary", key=f"roll_{code}"):
                        animate_die(die_ph)
                        roll_action(code, pid)
                        refresh()
                else:
                    st.caption(f"Esperando la tirada de {p['name']}… 🎲")
            else:
                st.info(f"🎲 Ha salido {room['last_roll']}: casilla **{pend['sq']}** ({fmt(pend['delta'])})")
                if can:
                    st.write(f"Tenías **{pend['before']}** puntos. Haz la cuenta en tu cabeza: ¿cuántos tienes ahora?")
                    with st.form(f"resp_{code}", clear_on_submit=True):
                        ans = st.number_input("Mis puntos ahora", min_value=0, step=1, value=0)
                        ok = st.form_submit_button("✅ Comprobar")
                    if ok:
                        if check_action(code, pid, int(ans)):
                            refresh()
                        else:
                            st.error("¡Casi! Inténtalo otra vez con calma. ✨")
                else:
                    st.caption(f"{p['name']} está haciendo la cuenta… 🧠")
            if is_host and not room["local"] and not can:
                if st.button("⏭️ Saltar turno (no está)", key=f"skip_{code}"):
                    skip_action(code)
                    refresh()

    if room["log"]:
        with st.expander("📝 Hoja de puntos", expanded=room["finished"]):
            st.dataframe(pd.DataFrame(room["log"]), hide_index=True)


def lobby():
    pid = st.session_state.pid
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏠 Crear una sala")
        modo = st.radio("¿Cómo jugáis?", ["Cada uno en su dispositivo (online)", "Todos en este dispositivo"])
        local = modo.startswith("Todos")
        if local:
            n = st.slider("Número de jugadores", 1, MAX_PLAYERS, 2)
            names = [st.text_input(f"Nombre del jugador {i + 1} {TOKENS[i]}", key=f"ln{i}") for i in range(n)]
        else:
            names = [st.text_input("Tu nombre", key="host_name")]
        if st.button("✨ Crear sala", type="primary"):
            names = [x.strip() or f"Jugador {i + 1}" for i, x in enumerate(names)]
            st.session_state.room = create_room(names, local, pid)
            st.rerun()
    with c2:
        st.subheader("🚪 Unirme a una sala")
        code_in = st.text_input("Código de la sala (4 letras)", value=st.query_params.get("sala", ""),
                                max_chars=4).upper().strip()
        name_in = st.text_input("Tu nombre", key="join_name").strip()
        if st.button("Unirme"):
            if len(code_in) != 4 or not name_in:
                st.error("Escribe el código de 4 letras y tu nombre.")
            else:
                ok, msg = join_room(code_in, name_in, pid)
                if ok:
                    st.session_state.room = code_in
                    st.rerun()
                else:
                    st.error(msg)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.session_state.setdefault("pid", uuid.uuid4().hex)
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(f'<div class="titulo">{TITULO}</div>', unsafe_allow_html=True)

tab_jugar, tab_tablero, tab_acciones, tab_normas, tab_marcadores = st.tabs(
    ["🎲 Jugar", "🗺️ Tablero", "📋 Acciones", "📜 Normas", "🏆 Marcadores"]
)

with tab_jugar:
    if st.session_state.get("room"):
        game_view(st.session_state.room)
    else:
        lobby()

with tab_tablero:
    st.markdown(board_html(), unsafe_allow_html=True)
    st.caption(FUENTES)
    st.download_button("🖨️ Descargar tablero para imprimir", printable_html(),
                       file_name="tablero_reino_magico.html", mime="text/html")
    st.subheader("🎲 Dado mágico (para jugar con el tablero de cartulina)")
    free_ph = st.empty()
    free_ph.markdown(die_html(st.session_state.get("free_roll")), unsafe_allow_html=True)
    if st.button("Tirar el dado", key="free_dice"):
        animate_die(free_ph)
        st.session_state.free_roll = random.randint(1, 6)
        free_ph.markdown(die_html(st.session_state.free_roll), unsafe_allow_html=True)

with tab_acciones:
    pos = [s for s in SQUARES if s[1] > 0]
    neg = [s for s in SQUARES if s[1] < 0]
    a1, a2 = st.columns(2)
    with a1:
        st.subheader("🌈 Acciones positivas")
        for n, p, e in sorted(pos, key=lambda s: -s[1]):
            st.write(f"{e} {n}: **{fmt(p)}**")
    with a2:
        st.subheader("⛈️ No tan buenas")
        for n, p, e in sorted(neg, key=lambda s: s[1]):
            st.write(f"{e} {n}: **{fmt(p)}**")

with tab_normas:
    st.subheader("📜 Normas del juego")
    for i, r in enumerate(RULES, 1):
        st.write(f"**{i}.** {r}")
    st.caption(FUENTES)

with tab_marcadores:
    st.subheader("🏆 Salón de la fama")
    hall = STORE["hall"]
    if hall:
        df = pd.DataFrame(hall)
        st.write("**Mejores puntuaciones**")
        st.dataframe(df.sort_values("Puntos", ascending=False).head(10), hide_index=True)
        st.write("**Últimas partidas**")
        st.dataframe(df.iloc[::-1].head(10), hide_index=True)
    else:
        st.info("Todavía no hay partidas terminadas. ¡Sé la primera persona en llegar a la Meta! 🌈")
    st.caption("Los marcadores se guardan mientras la app esté encendida; si Streamlit la reinicia, se borran.")
