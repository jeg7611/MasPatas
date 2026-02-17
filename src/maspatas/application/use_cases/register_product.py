from __future__ import annotations

from decimal import Decimal

from maspatas.application.dto.product_dto import RegisterProductInputDTO, RegisterProductOutputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.domain.entities.inventory import InventoryMovementType
from maspatas.domain.entities.product import Product
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.ports.concurrency import ConcurrencyControlPort
from maspatas.domain.ports.repositories import InventoryRepositoryPort, ProductRepositoryPort
from maspatas.domain.value_objects.common import Money, ProductId


class RegisterProductUseCase:
    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        inventory_repo: InventoryRepositoryPort,
        concurrency: ConcurrencyControlPort,
        authz: AuthorizationService,
    ) -> None:
        self._product_repo = product_repo
        self._inventory_repo = inventory_repo
        self._concurrency = concurrency
        self._authz = authz

    def execute(self, dto: RegisterProductInputDTO, role: Role) -> RegisterProductOutputDTO:
        self._authz.ensure_permission(role, "manage_inventory")

        if dto.initial_stock < 0:
            raise BusinessRuleViolation("No se permite stock inicial negativo")

        product_id = ProductId(dto.product_id)
        if self._product_repo.get_by_id(product_id) is not None:
            raise BusinessRuleViolation(f"Ya existe un producto con id {dto.product_id}")

        lock_key = f"product:{dto.product_id}"
        with self._concurrency.lock(lock_key):
            product = Product(
                id=product_id,
                name=dto.name,
                sku=dto.sku,
                price=Money(amount=Decimal(dto.price_amount), currency=dto.currency),
            )
            self._product_repo.save_product(product)

            if dto.initial_stock > 0:
                inventory = self._inventory_repo.get_inventory()
                inventory = inventory.apply_movement(
                    product_id=product.id,
                    movement_type=InventoryMovementType.ENTRADA,
                    quantity=dto.initial_stock,
                )
                self._inventory_repo.save_inventory(inventory)

            return RegisterProductOutputDTO(
                product_id=product.id.value,
                name=product.name,
                sku=product.sku,
                price_amount=str(product.price.amount),
                currency=product.price.currency,
                initial_stock=dto.initial_stock,
            )
