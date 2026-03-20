import streamlit as st
import requests

ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball"
    "/mens-college-basketball/scoreboard"
)


@st.cache_data(ttl=60)
def fetch_tournament_results():
    """Return {winner_name: headline} for completed March Madness games today."""
    try:
        response = requests.get(ESPN_SCOREBOARD, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching game data: {e}")
        return {}

    results = {}
    for event in data.get("events", []):
        comp = event["competitions"][0]
        if comp.get("type", {}).get("abbreviation") != "TRNMNT":
            continue
        if not comp["status"]["type"].get("completed", False):
            continue
        headline = comp.get("notes", [{}])[0].get("headline", "NCAA Tournament")
        for competitor in comp["competitors"]:
            if competitor.get("winner", False):
                name = competitor["team"]["displayName"]
                results[name] = headline

    return results


def find_match(guess, winners):
    guess_n = guess.lower().strip()
    for winner in winners:
        if guess_n in winner.lower() or winner.lower() in guess_n:
            return winner
    return None


# --- Page config ---
st.set_page_config(page_title="March Madness Guesser", page_icon="🏀", layout="centered")
st.title("🏀 March Madness Winner Guesser")
st.caption("Can you guess which teams won today's NCAA Tournament games?")

# --- Session state init ---
if "found" not in st.session_state:
    st.session_state.found = []
if "guesses" not in st.session_state:
    st.session_state.guesses = []  # list of (guess, correct) tuples

# --- Fetch data ---
winners = fetch_tournament_results()

if not winners:
    st.warning("No completed tournament games yet today. Check back later!")
    st.stop()

total = len(winners)
found = st.session_state.found
game_over = len(found) == total

# --- Progress ---
st.progress(len(found) / total)
st.markdown(f"**{len(found)} / {total}** winners found")

# --- Input ---
if not game_over:
    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Enter a college name:", placeholder="e.g. Duke")
        submitted = st.form_submit_button("Guess")

    if submitted and guess.strip():
        match = find_match(guess, winners)
        if not match:
            st.session_state.guesses.append((guess, False))
        elif match in found:
            st.info(f"You already found **{match}**!")
        else:
            st.session_state.found.append(match)
            st.session_state.guesses.append((match, True))
            st.rerun()

    # --- Show last few guesses ---
    if st.session_state.guesses:
        st.markdown("---")
        st.markdown("**Recent guesses:**")
        for g, correct in reversed(st.session_state.guesses[-5:]):
            if correct:
                st.success(f"✓ {g}")
            else:
                st.error(f"✗ {g}")

else:
    st.balloons()
    st.success(f"You found all {total} winners! Great job!")

# --- Found teams ---
if found:
    st.markdown("---")
    st.markdown("**Teams you've found:**")
    for name in found:
        st.markdown(f"- **{name}** — {winners[name]}")

# --- Hint expander ---
with st.expander("Hint: show regions with completed games"):
    regions = set(h.split(" - ")[1] for h in winners.values() if " - " in h)
    for r in sorted(regions):
        st.markdown(f"- {r}")

# --- Give up ---
if not game_over:
    st.markdown("---")
    if st.button("Give up / Show all winners"):
        for name, headline in winners.items():
            st.markdown(f"- **{name}** — {headline}")
