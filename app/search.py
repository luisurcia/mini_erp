"""Shared helper for text search on list screens. See #123."""

from sqlalchemy import or_


def search_ilike(query, term: str | None, *columns):
    """Narrow `query` to rows where any of `columns` contains `term`
    (case-insensitive substring match). An empty/blank term returns the
    query unchanged, so callers can pass it through unconditionally."""
    term = (term or "").strip()
    if not term:
        return query
    pattern = f"%{term}%"
    return query.filter(or_(*(column.ilike(pattern) for column in columns)))
