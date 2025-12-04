import math
import random
import matplotlib.pyplot as plt
random.seed(0)

PRODUCTS = ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11", "p12"]

FACTORY_PRODUCTS = {"F1": ["p1", "p2", "p3", "p4", "p5", "p6"],
    "F2": ["p7", "p8", "p9", "p10", "p11", "p12"],
    "F3": ["p4", "p5", "p6", "p7", "p8", "p9"],
    "F4": ["p10", "p11", "p12", "p1", "p2", "p3"]}

LEAD_TIMES = {"D1": {"F1": 16, "F2": 22, "F3": 20, "F4": 12},
    "D2": {"F1": 15, "F2": 16, "F3": 13, "F4": 19},
    "D3": {"F1": 14, "F2": 16.5, "F3": 20, "F4": 17},
    "D4": {"F1": 22, "F2": 13, "F3": 16.5, "F4": 18}}

DISTRIBUTOR_PRODUCT_FACTORY = {"D1": {
        "p1": "F1",
        "p2": "F1",
        "p3": "F1",
        "p4": "F1",
        "p5": "F1",
        "p6": "F1",
        "p7": "F2",
        "p8": "F2",
        "p9": "F2",
        "p10": "F2",
        "p11": "F2",
        "p12": "F2"},
    "D2": {
        "p1": "F1",
        "p2": "F1",
        "p3": "F1",
        "p4": "F1",
        "p5": "F1",
        "p6": "F1",
        "p7": "F2",
        "p8": "F2",
        "p9": "F2",
        "p10": "F2",
        "p11": "F2",
        "p12": "F2"},
    "D3": {
        "p1": "F4",
        "p2": "F4",
        "p3": "F4",
        "p4": "F3",
        "p5": "F3",
        "p6": "F3",
        "p7": "F3",
        "p8": "F3",
        "p9": "F3",
        "p10": "F4",
        "p11": "F4",
        "p12": "F4"},
    "D4": {
        "p1": "F4",
        "p2": "F4",
        "p3": "F4",
        "p4": "F3",
        "p5": "F3",
        "p6": "F3",
        "p7": "F3",
        "p8": "F3",
        "p9": "F3",
        "p10": "F4",
        "p11": "F4",
        "p12": "F4"}}

TOTAL_DAYS = 30


class Factory:

    def __init__(self, name, products):
        self.name = name
        self.products_produced = list(products)
        self.stock = {product: 0 for product in self.products_produced}
        self.pending_orders = []
        self.planned_deliveries = []
        self.production_per_day = [0 for day in range(TOTAL_DAYS)]

    def produce_some_products(self, day_index):
        seconds_in_day = 86400
        time_passed = 0
        mean_inter = 600  # seconds
        while time_passed < seconds_in_day:
            delta = random.expovariate(1.0 / mean_inter)
            time_passed += delta
            if time_passed < seconds_in_day:
                product = random.choice(self.products_produced)
                self.stock[product] += 1
                self.production_per_day[day_index] += 1

    #store orders that will be immediately processed and those that will need to wait
    def receive_order(self, distributor_name, product, quantity, current_day):
        order = {
            "distributor": distributor_name,
            "product": product,
            "quantity": quantity,
            "day": current_day,
        }
        self.pending_orders.append(order)

    #process as many orders as possible given current stock
    def process_orders(self, current_day):
        #orders we couldn’t fulfill today
        next_orders = []

        for order in self.pending_orders:
            product = order["product"]
            quantity = order["quantity"]
            distributor = order["distributor"]

            #lead time rounded up to full days
            hours = LEAD_TIMES[distributor][self.name]
            delivery_day = current_day + math.ceil(hours / 24.0)

            #if enough stock then reserve and schedule the delivery
            if self.stock.get(product) >= quantity:
                self.stock[product] -= quantity
                self.planned_deliveries.append(
                    {
                        "distributor": distributor,
                        "product": product,
                        "quantity": quantity,
                        "delivery_day": delivery_day,
                    }
                )
            else:
                next_orders.append(order)

        self.pending_orders = next_orders

    def get_due_deliveries_for_day(self, day_index):
        todays_deliveries = []
        remaining = []
        for delivery in self.planned_deliveries:
            if delivery["delivery_day"] == day_index:
                todays_deliveries.append(delivery)
            else:
                remaining.append(delivery)
        self.planned_deliveries = remaining
        return todays_deliveries



class Distributor:
    def __init__(self, name):
        self.name = name
        self.stock = {p: 0 for p in PRODUCTS}
        self.missed_wholesaler_orders = {p: 0 for p in PRODUCTS}
        self.orders_for_factories = []
        self.sales_per_day = {d: {p: 0 for p in PRODUCTS} for d in range(TOTAL_DAYS)}
        self.deliveries_per_day = {d: {p: 0 for p in PRODUCTS} for d in range(TOTAL_DAYS)}
        self.wholesaler_orders_per_day = {d: 0 for d in range(TOTAL_DAYS)}
        self.stock_total_per_day = []
        self.missed_demand_per_day = {d: 0 for d in range(TOTAL_DAYS)}

    #wholesaler orders are processed immediately (no delivery delay and no backorders)
    def receive_wholesaler_order(self, product, day_index):
        self.wholesaler_orders_per_day[day_index] += 1
        if self.stock.get(product) > 0:
            self.stock[product] -= 1
            self.sales_per_day[day_index][product] += 1
        else:
            self.missed_wholesaler_orders[product] += 1
            self.missed_demand_per_day[day_index] += 1

    def plan_initial_stock_order(self, day_index):
        #only for day 7
        if day_index == 7:
            for product in PRODUCTS:
                self.orders_for_factories.append({"product": product, "quantity": 10})

    def collect_missed_demand_into_orders(self):
        for product, quantity in self.missed_wholesaler_orders.items():
            if quantity > 0:
                self.orders_for_factories.append({"product": product, "quantity": quantity})
        self.missed_wholesaler_orders = {p: 0 for p in PRODUCTS}

    
    def send_orders_to_factories(self, factories, day_index):
        #we pass the parameter factories from the later Simulation so the distributor uses the shared factories.
        #keeping self.factories inside this class would create isolated copies, which is wrong.
    
        for order in self.orders_for_factories:
            target_factory = DISTRIBUTOR_PRODUCT_FACTORY[self.name][order["product"]]
            factories[target_factory].receive_order(
                self.name,
                order["product"],
                order["quantity"],
                day_index,
            )
        #reset orders list after sending
        self.orders_for_factories = []


    def receive_delivery(self, product, quantity, day_index):
        self.stock[product] += quantity
        self.deliveries_per_day[day_index][product] += quantity


class Wholesalers:

    #wholesalers creates random orders during the day
    def generate_orders_for_the_day(self, day_index, distributors):
        #we pass the parameter distributors from the later Simulation for the same reason as above with factories in the class distributor
        #keeping self.distributors inside this class would create isolated copies, which is wrong.

        seconds_in_day = 86400
        time_passed = 0

        #using a dict so we can access each distributor directly by its name (like "D1"),
        #makes everything easier to handle later in the simulation
        distributors_list = list(distributors.values())

        while time_passed < seconds_in_day:
            delta = random.uniform(600, 3600)
            time_passed += delta
            if time_passed < seconds_in_day:
                # pick distributor + product
                distributor = random.choice(distributors_list)
                product = random.choice(PRODUCTS)

                # distributor receives the order
                distributor.receive_wholesaler_order(product, day_index)

class Simulation:
    def __init__(self):
        self.factories = {}
        for name, products in FACTORY_PRODUCTS.items():
            self.factories[name] = Factory(name, products)

        self.distributors = {}
        for name in ["D1", "D2", "D3", "D4"]:
            self.distributors[name] = Distributor(name)

        self.wholesalers = Wholesalers()
        self.current_day = 0

    def run_one_day(self, day_index):

        # If we are in the first 7 days, factories only produce
        if day_index < 7:

            for factory in self.factories.values():
                factory.produce_some_products(day_index)

        # If we are exactly on the 8th day (day_index == 7)
        elif day_index == 7:

            # distributors make the initial order at 00:00
            for distributor in self.distributors.values():
                distributor.plan_initial_stock_order(day_index)

            # distributors send their morning orders to factories
            for distributor in self.distributors.values():
                distributor.send_orders_to_factories(self.factories, day_index)

            # factories process orders and plan deliveries
            for factory in self.factories.values():
                factory.process_orders(day_index)
            
            # no wholesalers this day

            # factories produce today
            for factory in self.factories.values():
                factory.produce_some_products(day_index)

        # If we are after the 8th day (day_index >= 8)
        else:

            # deliver products that arrived yesterday night
            for factory in self.factories.values():
                deliveries = factory.get_due_deliveries_for_day(day_index)
                for delivery in deliveries:
                    distributor = self.distributors[delivery["distributor"]]
                    distributor.receive_delivery(delivery["product"], delivery["quantity"], day_index)

            # collect missed demand into orders
            for distributor in self.distributors.values():
                distributor.collect_missed_demand_into_orders()

            # distributors send their morning orders to factories
            for distributor in self.distributors.values():
                distributor.send_orders_to_factories(self.factories, day_index)

            # factories process orders and plan deliveries
            for factory in self.factories.values():
                factory.process_orders(day_index)

            # wholesalers place random orders during the day
            self.wholesalers.generate_orders_for_the_day(day_index, self.distributors)
            
            # factories produce today
            for factory in self.factories.values():
                factory.produce_some_products(day_index)

    def run_simulation(self):
        for day_index in range(TOTAL_DAYS):
            self.current_day = day_index
            self.run_one_day(day_index)
            for distributor in self.distributors.values():
                total_stock = sum(distributor.stock.values())
                distributor.stock_total_per_day.append(total_stock)


if __name__ == "__main__":
    sim = Simulation()
    sim.run_simulation()


    # Analysis and plots
    days = list(range(TOTAL_DAYS))

    # 1) Total production per factory
    plt.figure(figsize=(8, 4))
    for factory_name in ["F1", "F2", "F3", "F4"]:
        production = sim.factories[factory_name].production_per_day
        plt.plot(days, production, label=factory_name)
    plt.title("Total production per factory")
    plt.xlabel("Day")
    plt.ylabel("Units produced")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # 2) Deliveries received by distributors
    plt.figure(figsize=(8, 4))
    for distributor_name in ["D1", "D2", "D3", "D4"]:
        distributor = sim.distributors[distributor_name]
        deliveries_per_day = [
            sum(distributor.deliveries_per_day[day].values()) for day in days
        ]
        plt.plot(days, deliveries_per_day, label=distributor_name)
    plt.title("Deliveries received by distributors")
    plt.xlabel("Day")
    plt.ylabel("Units delivered")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # 3) Wholesaler orders per distributor
    plt.figure(figsize=(8, 4))
    for distributor_name in ["D1", "D2", "D3", "D4"]:
        orders_per_day = [
            sim.distributors[distributor_name].wholesaler_orders_per_day[day]
            for day in days
        ]
        plt.plot(days, orders_per_day, label=distributor_name)
    plt.title("Wholesaler orders per distributor")
    plt.xlabel("Day")
    plt.ylabel("Orders")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # 4) Daily sales per distributor
    plt.figure(figsize=(8, 4))
    for distributor_name in ["D1", "D2", "D3", "D4"]:
        distributor = sim.distributors[distributor_name]
        sales_totals = [
            sum(distributor.sales_per_day[day].values()) for day in days
        ]
        plt.plot(days, sales_totals, label=distributor_name)
    plt.title("Daily sales per distributor")
    plt.xlabel("Day")
    plt.ylabel("Units sold")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # 5) Total stock per distributor
    plt.figure(figsize=(8, 4))
    for distributor_name in ["D1", "D2", "D3", "D4"]:
        stocks = sim.distributors[distributor_name].stock_total_per_day
        plt.plot(days, stocks, label=distributor_name)
    plt.title("Total stock per distributor")
    plt.xlabel("Day")
    plt.ylabel("Units in stock")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # 6) Missed demand per distributor
    plt.figure(figsize=(8, 4))
    for distributor_name in ["D1", "D2", "D3", "D4"]:
        distributor = sim.distributors[distributor_name]
        missed_per_day = [distributor.missed_demand_per_day[day] for day in days]
        plt.plot(days, missed_per_day, label=distributor_name)
    plt.title("Missed demand per distributor")
    plt.xlabel("Day")
    plt.ylabel("Missed demand")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.show()
    
