"""
tests/test_watchlist.py — CineLog

Tests for the watchlist service.
Follows the fixture and assertion patterns in tests/test_collection.py.
"""

import pytest
from extensions import db
from models import Film, WatchlistEntry
from services.watchlist_service import (
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist,
    AlreadyInWatchlistError,
    NotInWatchlistError,
)
from services.errors import FilmNotFoundError


# ── Deduplication ────────────────────────────────────────────────────────────

def test_add_to_watchlist_duplicate_raises(app, sample_user, sample_film):
    """
    Adding the same film twice should raise AlreadyInWatchlistError,
    not silently create a duplicate entry.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        with pytest.raises(AlreadyInWatchlistError):
            add_to_watchlist(user_id=sample_user, film_id=sample_film)

        # Confirm only one entry exists
        count = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).count()
        assert count == 1


def test_watchlist_unique_constraint_rejects_duplicate_rows(app, sample_user, sample_film):
    """
    The database itself should reject a second (user_id, film_id) row, so a
    duplicate can't slip in if two requests pass the service check at once.
    """
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        db.session.add(WatchlistEntry(user_id=sample_user, film_id=sample_film))
        db.session.commit()

        db.session.add(WatchlistEntry(user_id=sample_user, film_id=sample_film))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


# ── Nonexistent film ─────────────────────────────────────────────────────────

def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)


# ── get_watchlist sort order ─────────────────────────────────────────────────

def test_get_watchlist_returns_newest_first(app, sample_user):
    """
    get_watchlist() should return films sorted by date_added descending
    (most recently added first), matching get_collection().
    """
    with app.app_context():
        from datetime import datetime, timezone, timedelta

        film_a = Film(title="Alien", year=1979, genre="Horror")
        film_b = Film(title="Blade Runner", year=1982, genre="Sci-Fi")
        db.session.add_all([film_a, film_b])
        db.session.commit()

        earlier = datetime.now(timezone.utc) - timedelta(days=5)
        later = datetime.now(timezone.utc)

        entry_a = WatchlistEntry(user_id=sample_user, film_id=film_a.id, date_added=earlier)
        entry_b = WatchlistEntry(user_id=sample_user, film_id=film_b.id, date_added=later)
        db.session.add_all([entry_a, entry_b])
        db.session.commit()

        watchlist = get_watchlist(sample_user)
        titles = [f["title"] for f in watchlist]

        # Blade Runner was added later, so it should come first
        assert titles[0] == "Blade Runner"
        assert titles[1] == "Alien"


# ── remove_from_watchlist ────────────────────────────────────────────────────

def test_remove_from_watchlist_deletes_entry(app, sample_user, sample_film):
    """
    Removing a film that is on the watchlist should delete its entry and
    return True.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        assert remove_from_watchlist(user_id=sample_user, film_id=sample_film) is True

        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db is None


def test_remove_from_watchlist_not_present_raises(app, sample_user, sample_film):
    """
    Removing a film that isn't on the watchlist should raise
    NotInWatchlistError rather than failing silently.
    """
    with app.app_context():
        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(user_id=sample_user, film_id=sample_film)


def test_film_can_be_re_added_after_removal(app, sample_user, sample_film):
    """
    After a film is removed, adding it again should succeed: removal has to
    actually free the (user_id, film_id) slot that deduplication checks.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)
        remove_from_watchlist(user_id=sample_user, film_id=sample_film)

        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)
        assert entry.film_id == sample_film


# ── Visibility ───────────────────────────────────────────────────────────────

def test_add_to_watchlist_defaults_to_public(app, sample_user, sample_film):
    """
    With no public argument, a new entry should be public (the documented
    default from the Comment 4 decision).
    """
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)
        assert entry.public is True


def test_add_to_watchlist_can_be_private(app, sample_user, sample_film):
    """
    Passing public=False should store the entry as private.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film, public=False)

        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db.public is False


def test_add_endpoint_accepts_public_flag(client, sample_user, sample_film):
    """
    POST /watchlist/<user_id>/add should pass "public": false through to the
    stored entry and reject a non-boolean value with 400.
    """
    resp = client.post(
        f"/watchlist/{sample_user}/add",
        json={"film_id": sample_film, "public": False},
    )
    assert resp.status_code == 201
    assert resp.get_json()["public"] is False

    resp = client.post(
        f"/watchlist/{sample_user}/add",
        json={"film_id": sample_film, "public": "no"},
    )
    assert resp.status_code == 400
