import random

import pandas as pd
import streamlit as st

st.set_page_config(page_title="El Reino Mágico de los Puntos", page_icon="🦄", layout="wide")

TITULO = "🦄 El Reino Mágico de los Puntos 🧚"
START_POINTS = 100
COLS = 6
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
    "Cuando todos han llegado a la Meta, gana quien tiene más puntos.",
    "Si hay empate, ¡comparten la corona de unicornio! 👑",
]

FUENTES = (
    "Fuentes: libro de Matemáticas de 3.º de Primaria, página 43 (ejemplos de casillas), "
    "y las ideas de la clase sobre buenas acciones. Añade aquí las fuentes que hayas usado."
)

CSS = """
<style>
.board{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;max-width:900px;margin:auto}
.cell{border-radius:14px;padding:6px 4px;text-align:center;min-height:96px;display:flex;
flex-direction:column;justify-content:center;align-items:center;font-family:'Comic Sans MS',cursive,sans-serif;
border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.18)}
.cell .n{font-size:11px;opacity:.7;align-self:flex-start}
.cell .e{font-size:26px}
.cell .t{font-size:12px;line-height:1.1;color:#333;font-weight:bold}
.cell .p{font-size:20px;font-weight:bold}
.pos{background:linear-gradient(135deg,#d9f7e8,#b9ecd6)} .pos .p{color:#0a8a55}
.neg{background:linear-gradient(135deg,#ffe0e8,#ffc2d4)} .neg .p{color:#c0173f}
.special{background:linear-gradient(135deg,#efe0ff,#d5c0ff)} .special .p{color:#6a2fc0}
.tok{font-size:22px}
.titulo{text-align:center;font-size:34px;font-weight:bold;color:#9b4dca;font-family:'Comic Sans MS',cursive,sans-serif}
@media(max-width:600px){.cell{min-height:70px}.cell .t{font-size:9px}.cell .e{font-size:18px}.cell .p{font-size:14px}}
</style>
"""


def fmt(p):
    return f"{p:+d}".replace("-", "−") if p else ""


def board_html(players=None):
    players = players or []
    cells = []
    for i, (name, pts, emoji) in enumerate(SQUARES):
        r = i // COLS
        c = i % COLS if r % 2 == 0 else COLS - 1 - i % COLS
        cls = "pos" if pts > 0 else "neg" if pts < 0 else "special"
        toks = "".join(p["token"] for p in players if p["pos"] == i)
        cells.append(
            f'<div class="cell {cls}" style="grid-row:{r + 1};grid-column:{c + 1}">'
            f'<span class="n">{i}</span><span class="e">{emoji}</span>'
            f'<span class="t">{name}</span><span class="p">{fmt(pts)}</span>'
            f'<span class="tok">{toks}</span></div>'
        )
    return '<div class="board">' + "".join(cells) + "</div>"


def printable_html():
    return (
        "<html><head><meta charset='utf-8'><title>Tablero</title>" + CSS + "</head><body>"
        f"<div class='titulo'>{TITULO}</div><br>" + board_html() +
        f"<p style='text-align:center;font-family:sans-serif'>{FUENTES}</p>"
        "<h3 style='font-family:sans-serif'>Normas</h3><ol style='font-family:sans-serif'>"
        + "".join(f"<li>{r}</li>" for r in RULES) + "</ol></body></html>"
    )


def init_state():
    st.session_state.setdefault("players", [])
    st.session_state.setdefault("turn", 0)
    st.session_state.setdefault("pending", None)
    st.session_state.setdefault("log", [])
    st.session_state.setdefault("last_roll", None)
    st.session_state.setdefault("finished", False)


def next_turn():
    players = st.session_state.players
    if all(p["done"] for p in players):
        st.session_state.finished = True
        return
    for _ in range(len(players)):
        st.session_state.turn = (st.session_state.turn + 1) % len(players)
        if not players[st.session_state.turn]["done"]:
            return


def roll_dice():
    p = st.session_state.players[st.session_state.turn]
    roll = random.randint(1, 6)
    st.session_state.last_roll = roll
    p["pos"] = min(p["pos"] + roll, LAST)
    name, pts, emoji = SQUARES[p["pos"]]
    if p["pos"] == LAST:
        p["done"] = True
    if pts == 0:
        st.session_state.log.append(
            {"Jugador": p["name"], "Casilla": f"{emoji} {name}", "Puntos": 0, "Total": p["score"]}
        )
        next_turn()
    else:
        st.session_state.pending = {"before": p["score"], "delta": pts, "sq": f"{emoji} {name}"}


def check_answer(answer):
    pend = st.session_state.pending
    p = st.session_state.players[st.session_state.turn]
    expected = max(0, pend["before"] + pend["delta"])
    if answer == expected:
        p["score"] = expected
        st.session_state.log.append(
            {"Jugador": p["name"], "Casilla": pend["sq"], "Puntos": pend["delta"], "Total": expected}
        )
        st.session_state.pending = None
        next_turn()
        st.rerun()
    else:
        st.error("¡Casi! Inténtalo otra vez con calma. ✨")


init_state()
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(f'<div class="titulo">{TITULO}</div>', unsafe_allow_html=True)

tab_jugar, tab_tablero, tab_acciones, tab_normas = st.tabs(
    ["🎲 Jugar", "🗺️ Tablero", "📋 Acciones", "📜 Normas"]
)

with tab_jugar:
    players = st.session_state.players
    if not players:
        st.subheader("¿Quién juega?")
        n = st.slider("Número de jugadores", 1, 4, 2)
        names = [st.text_input(f"Nombre del jugador {i + 1} {TOKENS[i]}", key=f"n{i}") for i in range(n)]
        if st.button("✨ ¡Empezar el juego!"):
            st.session_state.players = [
                {"name": names[i].strip() or f"Jugador {i + 1}", "token": TOKENS[i],
                 "pos": 0, "score": START_POINTS, "done": False}
                for i in range(n)
            ]
            st.rerun()
    else:
        st.markdown(board_html(players), unsafe_allow_html=True)
        cols = st.columns(len(players))
        for col, p in zip(cols, players):
            col.metric(f"{p['token']} {p['name']}", f"{p['score']} pts", "🌈 en la meta" if p["done"] else None)

        if st.session_state.finished:
            st.balloons()
            ranking = sorted(players, key=lambda x: x["score"], reverse=True)
            best = ranking[0]["score"]
            winners = [p["name"] for p in ranking if p["score"] == best]
            st.success(f"👑 ¡Gana {' y '.join(winners)} con {best} puntos!")
        else:
            p = players[st.session_state.turn]
            st.subheader(f"Turno de {p['token']} {p['name']}")
            pend = st.session_state.pending
            if pend is None:
                if st.session_state.last_roll:
                    st.caption(f"Última tirada: {st.session_state.last_roll}")
                st.button("🎲 Tirar el dado", on_click=roll_dice)
            else:
                st.info(f"🎲 Has sacado {st.session_state.last_roll} y caes en **{pend['sq']}** ({fmt(pend['delta'])})")
                st.write(f"Tenías **{pend['before']}** puntos. Haz la cuenta en tu cabeza: ¿cuántos tienes ahora?")
                ans = st.number_input("Mis puntos ahora", min_value=0, step=1, key="ans")
                if st.button("✅ Comprobar"):
                    check_answer(int(ans))

        if st.session_state.log:
            st.subheader("📝 Hoja de puntos")
            st.dataframe(pd.DataFrame(st.session_state.log), use_container_width=True, hide_index=True)
        if st.button("🔄 Nueva partida"):
            for k in ["players", "turn", "pending", "log", "last_roll", "finished"]:
                del st.session_state[k]
            st.rerun()

with tab_tablero:
    st.markdown(board_html(), unsafe_allow_html=True)
    st.caption(FUENTES)
    st.download_button("🖨️ Descargar tablero para imprimir", printable_html(),
                       file_name="tablero_reino_magico.html", mime="text/html")

with tab_acciones:
    pos = [s for s in SQUARES if s[1] > 0]
    neg = [s for s in SQUARES if s[1] < 0]
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌈 Acciones positivas")
        for n, p, e in sorted(pos, key=lambda s: -s[1]):
            st.write(f"{e} {n}: **{fmt(p)}**")
    with c2:
        st.subheader("⛈️ No tan buenas")
        for n, p, e in sorted(neg, key=lambda s: s[1]):
            st.write(f"{e} {n}: **{fmt(p)}**")

with tab_normas:
    st.subheader("📜 Normas del juego")
    for i, r in enumerate(RULES, 1):
        st.write(f"**{i}.** {r}")
    st.caption(FUENTES)
