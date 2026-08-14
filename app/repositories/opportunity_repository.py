from app.models.opportunity import Opportunity
from app.repositories.base_repository import Repository


class OpportunityRepository(Repository[Opportunity]):
    def __init__(self):
        super().__init__(Opportunity)

    def get_all(self) -> list[Opportunity]:
        return Opportunity.query.order_by(Opportunity.created_at.desc()).all()

    def open_opportunities(self) -> list[Opportunity]:
        return Opportunity.query.filter(
            Opportunity.stage.in_(Opportunity.OPEN_STAGES)
        ).all()

    def by_stage(self, stage: str) -> list[Opportunity]:
        return Opportunity.query.filter_by(stage=stage).all()
