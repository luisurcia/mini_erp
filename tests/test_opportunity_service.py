import pytest

from app.exceptions import InsufficientStockError, InvalidStageTransitionError
from app.models.opportunity import Opportunity
from app.services.inventory_service import InventoryService
from app.services.opportunity_service import OpportunityService


def test_create_opportunity_defaults_to_new_stage(app, customer, product):
    service = OpportunityService()
    opp = service.create(
        customer_id=customer.id,
        product_id=product.id,
        quantity_requested=5,
        source=Opportunity.SOURCE_INSTAGRAM,
    )
    assert opp.stage == Opportunity.STAGE_NEW
    assert opp.is_open


def test_update_stage_valid_transition(app, customer, product):
    service = OpportunityService()
    opp = service.create(customer.id, product.id, 5)
    updated = service.update_stage(opp.id, Opportunity.STAGE_CONTACTED)
    assert updated.stage == Opportunity.STAGE_CONTACTED


def test_update_stage_invalid_stage_raises(app, customer, product):
    service = OpportunityService()
    opp = service.create(customer.id, product.id, 5)
    with pytest.raises(InvalidStageTransitionError):
        service.update_stage(opp.id, "not-a-real-stage")


def test_convert_to_sale_creates_sale_marks_won_and_consumes_stock(app, customer, product):
    service = OpportunityService()
    opp = service.create(customer.id, product.id, quantity_requested=4)

    sale = service.convert_to_sale(opp.id)

    assert opp.stage == Opportunity.STAGE_WON
    assert opp.sale_id == sale.id
    item = InventoryService().inventory_repo.get_by_product(product.id)
    assert item.quantity_on_hand == 46  # 50 - 4


def test_convert_to_sale_on_already_closed_opportunity_raises(app, customer, product):
    service = OpportunityService()
    opp = service.create(customer.id, product.id, quantity_requested=1)
    service.convert_to_sale(opp.id)

    with pytest.raises(InvalidStageTransitionError):
        service.convert_to_sale(opp.id)


def test_convert_to_sale_with_insufficient_stock_propagates_error(app, customer, product):
    service = OpportunityService()
    opp = service.create(customer.id, product.id, quantity_requested=9999)
    with pytest.raises(InsufficientStockError):
        service.convert_to_sale(opp.id)
