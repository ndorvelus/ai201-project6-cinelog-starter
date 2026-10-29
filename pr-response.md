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
**My position:**
**Reasoning:**
**Engagement with reviewer's point:**

## Comment 6 — Rebase
**What conflicted:**
**How I resolved it:**
**How I verified no conflict remains:**

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->