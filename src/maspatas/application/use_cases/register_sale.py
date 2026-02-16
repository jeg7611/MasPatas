from __future__ import annotations

from maspatas.application.dto.sale_dto import RegisterSaleInputDTO, RegisterSaleOutputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.domain.entities.inventory import InventoryMovementType
from maspatas.domain.entities.sale import SaleAggregate, SaleLine
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.ports.concurrency import ConcurrencyControlPort
from maspatas.domain.ports.repositories import (
    ClientRepositoryPort,
    InventoryRepositoryPort,
    ProductRepositoryPort,
    SaleRepositoryPort,
)
from maspatas.domain.value_objects.common import ClientId, ProductId


class RegisterSaleUseCase:
    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        client_repo: ClientRepositoryPort,
        inventory_repo: InventoryRepositoryPort,
        sale_repo: SaleRepositoryPort,
        concurrency: ConcurrencyControlPort,
        authz: AuthorizationService,
    ) -> None:
        self._product_repo = product_repo
        self._client_repo = client_repo
        self._inventory_repo = inventory_repo
        self._sale_repo = sale_repo
        self._concurrency = concurrency
        self._authz = authz

    def execute(self, dto: RegisterSaleInputDTO, role: Role) -> RegisterSaleOutputDTO:
        self._authz.ensure_permission(role, "register_sale")

        client = self._client_repo.get_by_id(ClientId(dto.client_id))
        if client is None:
            raise BusinessRuleViolation("Cliente no encontrado")

        lock_key = f"sale:{dto.sale_id}"
        with self._concurrency.lock(lock_key):
            inventory = self._inventory_repo.get_inventory()
            sale_lines: list[SaleLine] = []

            for line in dto.lines:
                product_id = ProductId(line.product_id)
                product = self._product_repo.get_by_id(product_id)
                if product is None:
                    raise BusinessRuleViolation(f"Producto no encontrado: {line.product_id}")

                current_item = inventory.get_item(product_id)
                if current_item.stock < line.quantity:
                    raise BusinessRuleViolation(
                        f"Stock insuficiente para {line.product_id}. Disponible={current_item.stock}, solicitado={line.quantity}"
                    )

                inventory = inventory.apply_movement(product_id, movement_type=InventoryMovementType.SALIDA, quantity=line.quantity)
                sale_lines.append(SaleLine(product_id=product_id, quantity=line.quantity, unit_price=product.price))

            sale = SaleAggregate(
                sale_id=dto.sale_id,
                client_id=client.id,
                lines=tuple(sale_lines),
            )
            self._sale_repo.save_sale(sale)
            self._inventory_repo.save_inventory(inventory)

            return RegisterSaleOutputDTO(
                sale_id=sale.sale_id,
                total_amount=str(sale.total.amount),
                currency=sale.total.currency,
            )
