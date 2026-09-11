from datetime import date

from app.exceptions import MiniErpError, NotFoundError
from app.models.sales import Sale
from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    """Customer-level operations that don't belong in a single CRUD route."""

    def __init__(self, customer_repo: CustomerRepository | None = None):
        self.customer_repo = customer_repo or CustomerRepository()

    def merge(self, discard_id: int, canonical_id: int) -> dict:
        """Fold `discard_id` into `canonical_id` (#138).

        The real-data migration (#121) created one `Customer` per literally
        distinct name found in the source spreadsheet — the same person
        typed a few different ways over a year ends up as several
        customers. Merging: every `Sale` that pointed at the discarded
        customer is reassigned to the canonical one, the discarded name is
        kept as a note on the canonical customer (so it's recognizable if
        that exact spelling resurfaces in a future load — there's no
        RUT/phone/email on migrated customers to cross-check against), and
        the discarded row is deleted. `Customer` has no `is_active` column
        (unlike Product/Supply/Warehouse/CustomerSegment) — nothing else
        references it once its sales move, so a hard delete is safe.
        """
        if discard_id == canonical_id:
            raise MiniErpError("Can't merge a customer into itself.")

        discard = self.customer_repo.get(discard_id)
        if discard is None:
            raise NotFoundError(f"Customer #{discard_id} not found")
        canonical = self.customer_repo.get(canonical_id)
        if canonical is None:
            raise NotFoundError(f"Customer #{canonical_id} not found")

        reassigned = Sale.query.filter_by(customer_id=discard.id).update(
            {"customer_id": canonical.id}
        )

        alias_note = (
            f"Unificado con «{discard.name}» (antes cliente #{discard.id} "
            f"aparte) el {date.today().isoformat()}."
        )
        canonical.notes = (
            f"{canonical.notes}\n{alias_note}" if canonical.notes else alias_note
        )

        self.customer_repo.delete(discard)
        self.customer_repo.commit()

        return {
            "canonical": canonical,
            "discarded_name": discard.name,
            "reassigned_sales": reassigned,
        }
