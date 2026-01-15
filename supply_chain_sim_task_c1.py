import random
import heapq
import numpy as np

PRODUCTS = [
    "p1",
    "p2",
    "p3",
    "p4",
    "p5",
    "p6",
    "p7",
    "p8",
    "p9",
    "p10",
    "p11",
    "p12",
]

FACTORY_PRODUCTS = {
    "F1": ["p1", "p2", "p3", "p4", "p5", "p6"],
    "F2": ["p7", "p8", "p9", "p10", "p11", "p12"],
    "F3": ["p4", "p5", "p6", "p7", "p8", "p9"],
    "F4": ["p10", "p11", "p12", "p1", "p2", "p3"],
}

LEAD_TIMES = {
    "D1": {"F1": 16, "F2": 22, "F3": 20, "F4": 12},
    "D2": {"F1": 15, "F2": 16, "F3": 13, "F4": 19},
    "D3": {"F1": 14, "F2": 16.5, "F3": 20, "F4": 17},
    "D4": {"F1": 22, "F2": 13, "F3": 16.5, "F4": 18},
}

TOTAL_DAYS = 30
END_TIME = TOTAL_DAYS * 24


class Factory:
    def __init__(self, name, products):
        self.name = name
        self.products_produced = list(products)
        self.stock = {p: 0 for p in self.products_produced}

    def produce_one_product(self):
        chosen = random.choice(self.products_produced)
        self.stock[chosen] += 1


class Distributor:
    def __init__(self, name):
        self.name = name
        self.stock = {p: 0 for p in PRODUCTS}
        self.missed_wholesaler_orders = {p: 0 for p in PRODUCTS}
        self.orders_for_factories = []
        self.postponed_orders = []

        self.sales_per_day = {d: {p: 0 for p in PRODUCTS} for d in range(TOTAL_DAYS)}
        self.stock_total_per_day = []
        self.cost_per_delivery_per_day = {d: {p: 0 for p in PRODUCTS} for d in range(TOTAL_DAYS)}
        self.cost_storage_per_day = {d: 0 for d in range(TOTAL_DAYS)}
        self.total_cost_per_day = {d: 0 for d in range(TOTAL_DAYS)}

    def receive_wholesaler_order(self, product, current_time, day_index, log_fn):
        if self.stock.get(product) > 0:
            self.stock[product] -= 1
            self.sales_per_day[day_index][product] += 1
            if self.name == "D1":
                log_fn(current_time)
        else:
            self.missed_wholesaler_orders[product] += 1

    def plan_initial_stock_order(self, day_index):
        if day_index == 7:
            for p in PRODUCTS:
                self.orders_for_factories.append({"product": p, "quantity": 10})

    def calculate_storage_costs(self, day_index):
        total = sum(self.stock[p] for p in PRODUCTS)
        self.cost_storage_per_day[day_index] += total

    def collect_all_demand_into_orders(self, day_index):
        for product, missed in self.missed_wholesaler_orders.items():
            sold_prev_day = self.sales_per_day[day_index - 1][product] if day_index > 0 else 0
            total_order = missed + sold_prev_day
            if total_order > 0:
                self.orders_for_factories.append({"product": product, "quantity": total_order})
        self.missed_wholesaler_orders = {p: 0 for p in PRODUCTS}

    def send_orders_with_lead_time_priority(self, factories, day_index, current_time, schedule_delivery_fn):
        new_postponed = []
        for order in self.orders_for_factories:
            product = order["product"]
            quantity = order["quantity"]
            # candidate factories producing this product
            candidates = [f for f, plist in FACTORY_PRODUCTS.items() if product in plist]
            # sort by lead time for this distributor
            candidates.sort(key=lambda f: LEAD_TIMES[self.name][f])

            fulfilled = False
            for f in candidates:
                available = factories[f].stock.get(product, 0)
                if available >= quantity:
                    factories[f].stock[product] -= quantity
                    lead_hours = LEAD_TIMES[self.name][f]
                    delivery_time = current_time + lead_hours
                    schedule_delivery_fn(delivery_time, self.name, product, quantity)
                    # cost proportional to lead time (same rule as other tasks)
                    self.cost_per_delivery_per_day[day_index][product] += 10 * lead_hours
                    fulfilled = True
                    break
            if not fulfilled:
                # postpone to next day
                new_postponed.append(order)
        # carry over postponed orders
        self.orders_for_factories = new_postponed

    def receive_delivery(self, product, quantity, current_time, day_index, log_fn):
        self.stock[product] += quantity
        if self.name == "D1":
            log_fn(current_time)

    def calculate_total_costs_per_day(self, day_index):
        delivery_costs = sum(self.cost_per_delivery_per_day[day_index].values())
        storage_costs = self.cost_storage_per_day[day_index]
        self.total_cost_per_day[day_index] = delivery_costs + storage_costs


class Wholesalers:
    def create_order(self, distributors, current_time, day_index, log_fn):
        distributors_list = list(distributors.values())
        distributor = random.choice(distributors_list)
        product = random.choice(PRODUCTS)
        distributor.receive_wholesaler_order(product, current_time, day_index, log_fn)


class Simulation:
    def __init__(self):
        self.factories = {name: Factory(name, FACTORY_PRODUCTS[name]) for name in FACTORY_PRODUCTS}
        self.distributors = {name: Distributor(name) for name in ["D1", "D2", "D3", "D4"]}
        self.wholesalers = Wholesalers()
        self.event_queue = []
        self.current_time = 0
        self.d1_stock_log = []
        self.event_counter = 0

    def log_d1_stock(self, time_value):
        total_stock = sum(self.distributors["D1"].stock[p] for p in self.distributors["D1"].stock)
        self.d1_stock_log.append((time_value, total_stock))

    def schedule_event(self, time_value, event_type, data):
        self.event_counter += 1
        new_type = event_type + "_" + str(self.event_counter)
        heapq.heappush(self.event_queue, (time_value, new_type, data))

    def schedule_next_factory_production(self, factory_name, base_time):
        delta_seconds = random.expovariate(1 / 600)
        next_time = base_time + (delta_seconds / 3600.0)
        if next_time <= END_TIME:
            self.schedule_event(next_time, "factory_production", {"factory": factory_name})

    def schedule_delivery(self, delivery_time, distributor, product, quantity):
        if delivery_time <= END_TIME:
            self.schedule_event(delivery_time, "delivery", {"distributor": distributor, "product": product, "quantity": quantity})

    def schedule_next_wholesaler_order(self, base_time):
        delta_hours = random.uniform(600, 3600) / 3600.0
        next_time = base_time + delta_hours
        if next_time <= END_TIME:
            self.schedule_event(next_time, "wholesaler_order", {})

    def handle_factory_production(self, data):
        name = data["factory"]
        self.factories[name].produce_one_product()
        self.schedule_next_factory_production(name, self.current_time)

    def handle_delivery(self, data):
        dist_name = data["distributor"]
        product = data["product"]
        quantity = data["quantity"]
        day_index = int(self.current_time // 24)
        self.distributors[dist_name].receive_delivery(product, quantity, self.current_time, day_index, self.log_d1_stock)

    def handle_wholesaler_order(self):
        day_index = int(self.current_time // 24)
        self.wholesalers.create_order(self.distributors, self.current_time, day_index, self.log_d1_stock)
        self.schedule_next_wholesaler_order(self.current_time)

    def handle_daily_order_event(self, data):
        day = data["day"]
        # per-day stock total
        for distributor in self.distributors.values():
            total_stock = sum(distributor.stock[p] for p in distributor.stock)
            distributor.stock_total_per_day.append(total_stock)
        # storage cost
        for distributor in self.distributors.values():
            distributor.calculate_storage_costs(day)
        # initial orders on day 7
        if day == 7:
            for distributor in self.distributors.values():
                distributor.plan_initial_stock_order(day)
        else:
            for distributor in self.distributors.values():
                distributor.collect_all_demand_into_orders(day)
        # send orders using lead-time priority
        for distributor in self.distributors.values():
            distributor.send_orders_with_lead_time_priority(self.factories, day, self.current_time, self.schedule_delivery)
        # daily costs
        for distributor in self.distributors.values():
            distributor.calculate_total_costs_per_day(day)

    def first_events(self):
        for name in self.factories:
            self.schedule_next_factory_production(name, 0)
        for d in range(7, TOTAL_DAYS):
            self.schedule_event(d * 24, "daily_order", {"day": d})
        self.schedule_next_wholesaler_order(8 * 24)
        self.log_d1_stock(0)

    def run(self):
        self.first_events()
        while len(self.event_queue) > 0:
            time_value, event_type, data = heapq.heappop(self.event_queue)
            if time_value > END_TIME:
                break
            self.current_time = time_value
            base_type = event_type.rsplit("_", 1)[0]
            if base_type == "factory_production":
                self.handle_factory_production(data)
            elif base_type == "delivery":
                self.handle_delivery(data)
            elif base_type == "wholesaler_order":
                self.handle_wholesaler_order()
            elif base_type == "daily_order":
                self.handle_daily_order_event(data)


if __name__ == "__main__":
    C = []
    N = []
    R = []
    for i in range(100):
        random.seed(i)
        sim_i = Simulation()
        sim_i.run()
        d1 = sim_i.distributors["D1"]
        Ci = sum(d1.total_cost_per_day.values())
        Ni = sum(d1.sales_per_day[d][p] for d in range(TOTAL_DAYS) for p in PRODUCTS)
        Ri = Ci / Ni if Ni > 0 else float('inf')
        C.append(Ci)
        N.append(Ni)
        R.append(Ri)

    print("Maximum Cost C:", max(C))
    print("Minimum Cost C:", min(C))
    print("Average Cost C:", sum(C) / len(C))
    print("Deviation Cost C:", np.std(C))
    print("\n")
    print("Maximum Number of Sales N:", max(N))
    print("Minimum Number of Sales N:", min(N))
    print("Average Number of Sales N:", sum(N) / len(N))
    print("Deviation Number of Sales N:", np.std(N))
    print("\n")
    print("Maximum Ratio R:", max(R))
    print("Minimum Ratio R:", min(R))
    print("Average Ratio R:", sum(R) / len(R))
    print("Deviation Ratio R:", np.std(R))
