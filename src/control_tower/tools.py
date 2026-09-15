"""Capabilities de leitura. Não executam compras, transferências ou decisões."""
import csv
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from .models import Carrier, CustomerOrder, Incident, Inventory, Policies, ProductionOrder, Stock, Supplier

class Tools:
    def __init__(self, root: Path):
        self.root = root
        self.suppliers = self._rows("suppliers", Supplier)
        self.inventory = self._rows("inventory", Inventory)
        self.production = self._rows("production_orders", ProductionOrder)
        self.customers = self._rows("customer_orders", CustomerOrder)
        self.carriers = self._rows("carriers", Carrier)
        self.policies = Policies.model_validate_json((root / "data/policies.json").read_text())
        for rows, key in [(self.suppliers, "supplier_id"), (self.production, "order_id"), (self.customers, "order_id")]:
            ids = [getattr(row, key) for row in rows]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Identificadores duplicados: {key}")
        stock_keys = [(r.plant, r.material) for r in self.inventory]
        if len(stock_keys) != len(set(stock_keys)):
            raise ValueError("Estoque duplicado por planta/material")
        for order in self.production:
            self.get_stock(order.material, order.plant)
            customer = self.get_customer_order(order.customer_order)
            if (order.product, order.quantity, order.priority) != (customer.product, customer.quantity, customer.priority):
                raise ValueError(f"Pedido inconsistente: {order.order_id}")
            if order.production_date + timedelta(days=1) > customer.delivery_date:
                raise ValueError("Entrega planejada não comporta um dia de transporte após produção")

    def _rows(self, name, model):
        with (self.root / f"data/{name}.csv").open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if set(reader.fieldnames or []) != set(model.model_fields):
                raise ValueError(f"Cabeçalho inválido: {name}.csv")
            rows = tuple(model.model_validate(row) for row in reader)
            if not rows:
                raise ValueError(f"Fixture incompleto: {name}.csv está vazio")
            return rows

    def get_stock(self, material: str, plant: str) -> Stock:
        row = next((r for r in self.inventory if (r.material, r.plant) == (material, plant)), None)
        if row is None:
            raise ValueError(f"Estoque não cadastrado: {material}/{plant}")
        available = row.quantity - row.reserved_quantity
        return Stock(plant=plant, material=material, available_units=available,
                     transferable_without_safety_stock_units=max(0, available-row.safety_stock))

    def get_supplier(self, supplier_id: str) -> Supplier:
        return self._one(self.suppliers, "supplier_id", supplier_id)

    def get_customer_order(self, order_id: str) -> CustomerOrder:
        return self._one(self.customers, "order_id", order_id)

    @staticmethod
    def _one(rows, key, value):
        row = next((r for r in rows if getattr(r, key) == value), None)
        if row is None:
            raise ValueError(f"Identificador desconhecido: {value}")
        return row

    def get_orders(self, material: str, plant: str) -> tuple[ProductionOrder, ...]:
        """Ordens relacionadas por material/planta; não confirma atraso ou impacto."""
        return tuple(r for r in self.production if r.material == material and r.plant == plant)

    def get_alternative_suppliers(self, material: str, exclude_supplier_id: str) -> tuple[Supplier, ...]:
        self.get_supplier(exclude_supplier_id)
        return tuple(r for r in self.suppliers if r.material == material and r.supplier_id != exclude_supplier_id)

    def get_routes(self, origin: str, destination: str) -> tuple[Carrier, ...]:
        return tuple(r for r in self.carriers if r.origin == origin and r.destination == destination)

    def calculate_penalty(self, order_id: str, delay_days: int) -> Decimal:
        if type(delay_days) is not int or delay_days < 0:
            raise ValueError("Dias de atraso devem ser um inteiro não negativo")
        return self.get_customer_order(order_id).sla_penalty_brl_per_day * delay_days

    def load_incident(self, path: Path) -> Incident:
        incident = Incident.model_validate_json(path.read_text(encoding="utf-8"))
        if self.get_supplier(incident.supplier_id).material != incident.material:
            raise ValueError("Material incompatível com fornecedor")
        self.get_stock(incident.material, incident.plant)
        if not self.get_orders(incident.material, incident.plant):
            raise ValueError("Incidente sem ordens relacionadas")
        return incident
