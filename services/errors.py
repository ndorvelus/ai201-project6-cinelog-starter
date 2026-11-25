"""
services/errors.py — CineLog

Exceptions shared by more than one feature's service layer. Feature-specific
errors (AlreadyInCollectionError, AlreadyInWatchlistError, ...) stay in their
own service modules.
"""


class FilmNotFoundError(Exception):
    """Raised when a film_id does not exist in the database."""
    pass
