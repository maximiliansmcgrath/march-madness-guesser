import requests


ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball"
    "/mens-college-basketball/scoreboard"
)


def fetch_tournament_results():
    """Return a dict of {winner_name: headline} for completed March Madness games today."""
    try:
        response = requests.get(ESPN_SCOREBOARD, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return {}

    results = {}
    for event in data.get("events", []):
        comp = event["competitions"][0]

        # Only NCAA tournament games
        if comp.get("type", {}).get("abbreviation") != "TRNMNT":
            continue

        # Only completed games
        if not comp["status"]["type"].get("completed", False):
            continue

        headline = comp.get("notes", [{}])[0].get("headline", "NCAA Tournament")
        for competitor in comp["competitors"]:
            if competitor.get("winner", False):
                name = competitor["team"]["displayName"]
                results[name] = headline

    return results


def normalize(name):
    return name.lower().strip()


def find_match(guess, winners):
    """Case-insensitive partial match against winner names."""
    guess_n = normalize(guess)
    for winner in winners:
        if guess_n in normalize(winner) or normalize(winner) in guess_n:
            return winner
    return None


def play(winners):
    found = set()
    total = len(winners)

    print(f"\n{total} game(s) completed so far today. Guess the winning teams!\n")
    print("Commands: 'hint' to see regions played, 'quit' to give up\n")

    while len(found) < total:
        guess = input("Guess a winner: ").strip()
        if not guess:
            continue

        if guess.lower() == "quit":
            remaining = [w for w in winners if w not in found]
            print(f"\nYou got {len(found)}/{total}. Missed: {', '.join(remaining)}")
            return

        if guess.lower() == "hint":
            regions = set(h.split(" - ")[1] for h in winners.values() if " - " in h)
            print(f"Regions with completed games: {', '.join(sorted(regions))}\n")
            continue

        match = find_match(guess, winners)
        if not match:
            print(f"  Nope. '{guess}' didn't win a March Madness game today.\n")
        elif match in found:
            print(f"  You already found {match}!\n")
        else:
            found.add(match)
            remaining = total - len(found)
            print(f"  Correct! {match} won ({winners[match]})")
            if remaining:
                print(f"  {remaining} winner(s) still to find.\n")

    print(f"\nYou found all {total} winner(s) today! Great job!")


def main():
    print("=== March Madness Winner Guesser ===")
    print("Fetching today's NCAA Tournament results...")

    winners = fetch_tournament_results()

    if not winners:
        print("No completed tournament games yet today. Check back later!")
        return

    play(winners)


if __name__ == "__main__":
    main()
