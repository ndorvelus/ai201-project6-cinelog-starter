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
**What I did:**
**How I verified:**

## Comment 4 — Default visibility
**My position:**
**Reasoning:**
**Tradeoff acknowledged:**

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