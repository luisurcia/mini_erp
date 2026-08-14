from app.exceptions import InvalidStageTransitionError, NotFoundError
from app.models.opportunity import Opportunity
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.sales_service import SalesService


class OpportunityService:
    """Manages the request/lead pipeline and converting a won request into
    a real Sale."""

    def __init__(
        self,
        opportunity_repo: OpportunityRepository | None = None,
        sales_service: SalesService | None = None,
    ):
        self.opportunity_repo = opportunity_repo or OpportunityRepository()
        self.sales_service = sales_service or SalesService()

    def create(
        self,
        customer_id: int,
        product_id: int | None,
        quantity_requested: int,
        source: str = Opportunity.SOURCE_OTHER,
        notes: str | None = None,
    ) -> Opportunity:
        opportunity = Opportunity(
            customer_id=customer_id,
            product_id=product_id,
            quantity_requested=quantity_requested,
            source=source,
            notes=notes,
            stage=Opportunity.STAGE_NEW,
        )
        self.opportunity_repo.add(opportunity)
        self.opportunity_repo.commit()
        return opportunity

    def update_stage(self, opportunity_id: int, new_stage: str) -> Opportunity:
        opportunity = self._get_or_raise(opportunity_id)
        if new_stage not in Opportunity.STAGES:
            raise InvalidStageTransitionError(f"'{new_stage}' is not a valid stage")
        if not opportunity.is_open:
            raise InvalidStageTransitionError(
                f"Opportunity #{opportunity_id} is already closed ({opportunity.stage})"
            )
        opportunity.stage = new_stage
        self.opportunity_repo.commit()
        return opportunity

    def convert_to_sale(self, opportunity_id: int):
        opportunity = self._get_or_raise(opportunity_id)
        if not opportunity.is_open:
            raise InvalidStageTransitionError(
                f"Opportunity #{opportunity_id} is already closed ({opportunity.stage})"
            )
        if opportunity.product_id is None:
            raise InvalidStageTransitionError(
                "Opportunity has no product selected, cannot convert to a sale"
            )

        sale = self.sales_service.record_sale(
            customer_id=opportunity.customer_id,
            items=[
                {
                    "product_id": opportunity.product_id,
                    "quantity": opportunity.quantity_requested,
                }
            ],
            notes=f"Converted from opportunity #{opportunity.id}",
        )

        opportunity.stage = Opportunity.STAGE_WON
        opportunity.sale_id = sale.id
        self.opportunity_repo.commit()
        return sale

    def open_opportunities(self) -> list[Opportunity]:
        return self.opportunity_repo.open_opportunities()

    def _get_or_raise(self, opportunity_id: int) -> Opportunity:
        opportunity = self.opportunity_repo.get(opportunity_id)
        if opportunity is None:
            raise NotFoundError(f"Opportunity #{opportunity_id} not found")
        return opportunity
