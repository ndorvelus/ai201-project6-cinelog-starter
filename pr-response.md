# PR Response Doc — CineLog Watchlist Feature

## AI Usage
<!-- Fill in at the end — how you used AI tools during this project -->

## Comment 1 — Rename
**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` and updated its import and call in the watchlist route.
**How I verified:** I searched the repo and found no remaining references to the old name, and all 4 tests passed.

## Comment 2 — Deduplication
**What I did:** I followed the pattern in `add_to_collection()` in `services/collection_service.py`, which checks for an existing `CollectionEntry` with the same `user_id` and `film_id` and, if one is found, raises `AlreadyInCollectionError` without saving anything, which the collection route returns as a 409 Conflict. I copied that into `add_to_watchlist()`: it now queries for an existing `WatchlistEntry` with the same `user_id` and `film_id`, raises a new `AlreadyInWatchlistError` before creating a duplicate, and the watchlist route catches it and returns 409.

**How I verified:** Adding the same film twice returned 201 the first time and 409 the second, and all existing tests still passed.

## Comment 3 — Missing test
**What I did:** I added `test_add_to_watchlist_nonexistent_film_raises` in `tests/test_watchlist.py`, mirroring `test_add_to_collection_nonexistent_film_raises` with the same `app`/`sample_user` fixtures and a `pytest.raises(FilmNotFoundError)` assertion.
**How I verified:** I ran `pytest tests/test_watchlist.py -v` and the new test passed, and the full suite passed with 5 tests.

## Comment 4 — Default visibility
**My position:** I'm keeping `public=True` as the default for watchlist entries.

**Reasoning:** I'm optimizing for the user who comes to CineLog to share and discover films with friends, which is the core loop of social film-logging apps like Letterboxd, where watchlists are public by default. A watchlist is low-sensitivity: it's a list of films someone wants to see, not a record of what they did, so showing it by default lets friends see what someone is excited about, suggest watching something together, and gives the app more signal for recommendations. Defaults are sticky, so if entries started private most users would never change them, and any social feature built on watchlists would launch empty.

**Tradeoff acknowledged:** Defaulting to `public=False` follows privacy-by-default and protects users who don't expect their list to be visible; someone who adds a film they'd rather keep to themselves and later finds it public loses trust in the app in a way that's hard to win back. That risk is real in this PR, because users currently have no way to change visibility: no endpoint sets `public`, and `GET /watchlist/<user_id>` returns every entry regardless of the flag. So `public=True` is only the right default if a follow-up adds a per-entry toggle and filters private entries out of other users' views; if that can't ship soon, I'd switch the default to `False` until it does.

## Comment 5 — Sort order
**My position:** I switched `get_watchlist()` to sort by date added, newest first.

**Reasoning:** A watchlist is a queue of intent, and the films a user added most recently are the ones they're most likely to act on next, so they belong at the top; alphabetical order buries a film added yesterday under everything that starts with "A".

**Engagement with reviewer's point:** I agree with the maintainer that the watchlist should match `get_collection()`, which already sorts by `date_added` descending, because two list endpoints in the same API returning different orders is a surprise for any client. Alphabetical order's real strength is finding a specific film in a long list, but that's a search or filter feature, not something the default order should give up recency for, and clients can still sort by title since every item includes it. I added `test_get_watchlist_returns_newest_first`, which mirrors the collection's sort test and fails under the old alphabetical order.

## Comment 6 — Rebase
**What conflicted:** I rebased `feature/watchlist` onto `main`, which had landed `57ec3f9` ("refactor: migrate film IDs from integer to UUID"). The rebase stopped on my first commit (`9eafe68`) with one conflict in `models.py` on `WatchlistEntry.film_id`: `main` had changed it to `db.String(36)` to match the new UUID `Film.id`, while my branch still declared it `db.Integer` and had added `index=True`. Two lines in my watchlist code also still described integer IDs without conflicting: the `film_id (int)` docstring in `services/watchlist_service.py` and the `{ "film_id": <int> }` request body in `routes/watchlist/watchlist.py`.

**How I resolved it:** I kept `main`'s `db.String(36)` type, since a foreign key has to match the type of `Film.id`, and kept my `index=True` because watchlist lookups filter on `film_id`, so the resolved line is `db.Column(db.String(36), db.ForeignKey("film.id"), nullable=False, index=True)`. I also updated the service docstring to `film_id (str): UUID of the film.` and the route body to `{ "film_id": "<uuid>" }`, staged the files, and ran `git rebase --continue`; the remaining six commits replayed with no further conflicts.

**How I verified no conflict remains:** On the rebased tip I searched every `.py` file for leftover `<<<<<<<`/`=======`/`>>>>>>>` markers and found none, and searched the models, services, and routes for integer film-ID references (`db.Integer` foreign keys, `(int)`, `<int>`) and found none. `git diff main -- models.py` shows my only change to the model is the added `index=True`, so I didn't undo any of the refactor. The full test suite passed (6 tests), including the watchlist tests, which already use a UUID string as the nonexistent `film_id`.

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->