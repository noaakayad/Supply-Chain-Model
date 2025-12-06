import random
import heapq
import matplotlib.pyplot as plt
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

DISTRIBUTOR_PRODUCT_FACTORY = {
    "D1": {
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
        "p12": "F2",
    },
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
        "p12": "F2",
    },
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
        "p12": "F4",
    },
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
        "p12": "F4",
    },
}

TOTAL_DAYS = 30
END_TIME = TOTAL_DAYS * 24  


class Factory:
    def __init__(self, name, products):
        self.name = name

        #list of products this factory can produce
        self.products_produced = []
        for p in products:
            self.products_produced.append(p)

        #initial stock: 0 for each product
        self.stock = {}
        for p in self.products_produced:
            self.stock[p] = 0

        #orders waiting to be processed
        self.pending_orders = []

    #produce a single random product
    def produce_one_product(self):
        chosen = random.choice(self.products_produced)
        self.stock[chosen] += 1

    #store incoming orders
    def receive_order(self, distributor_name, product, quantity):
        new_order = {}
        new_order["distributor"] = distributor_name
        new_order["product"] = product
        new_order["quantity"] = quantity

        self.pending_orders.append(new_order)

    #try to fulfill orders with current stock
    def process_orders(self, current_time, schedule_delivery_fn):

        #orders that remain unfulfilled
        remaining_orders = []

        for order in self.pending_orders:
            prod = order["product"]
            qty = order["quantity"]
            dist = order["distributor"]

            #if enough stock, schedule delivery
            if self.stock.get(prod, 0) >= qty:
                self.stock[prod] -= qty

                #compute delivery time based on lead hours
                lead_hours = LEAD_TIMES[dist][self.name]
                delivery_time = current_time + lead_hours

                #call the simulation to actually schedule event
                schedule_delivery_fn(delivery_time, dist, prod, qty)

            else:
                #not enough stock, keep order for later
                remaining_orders.append(order)

        self.pending_orders = remaining_orders

class Distributor:
    def __init__(self, name):
        self.name = name

        #initial stock for all products
        self.stock = {}
        for p in PRODUCTS:
            self.stock[p] = 0

        #track missed wholesaler orders
        self.missed_wholesaler_orders = {}
        for p in PRODUCTS:
            self.missed_wholesaler_orders[p] = 0

        #orders that will later be sent to factories
        self.orders_for_factories = []

        #sales counted per day and per product
        self.sales_per_day = {}
        for d in range(TOTAL_DAYS):
            self.sales_per_day[d] = {}
            for p in PRODUCTS:
                self.sales_per_day[d][p] = 0

        #total stock per day for plotting
        self.stock_total_per_day = []

        #delivery cost per day per product
        self.cost_per_delivery_per_day = {}
        for d in range(TOTAL_DAYS):
            self.cost_per_delivery_per_day[d] = {}
            for p in PRODUCTS:
                self.cost_per_delivery_per_day[d][p] = 0

        #storage cost accumulated per day
        self.cost_storage_per_day = {}
        for d in range(TOTAL_DAYS):
            self.cost_storage_per_day[d] = 0

        #total cost = delivery + storage
        self.total_cost_per_day = {}
        for d in range(TOTAL_DAYS):
            self.total_cost_per_day[d] = 0

    #wholesaler orders are handled immediately (no delay)
    def receive_wholesaler_order(self, product, current_time, day_index, log_fn):
        if self.stock.get(product) > 0:

            #we can deliver
            self.stock[product] -= 1

            self.sales_per_day[day_index][product] += 1

            #log only for D1
            if self.name == "D1":
                log_fn(current_time)

        else:
            #we had no stock, missed order
            self.missed_wholesaler_orders[product] += 1

    #distributors place initial order on day 7 at 00:00
    def plan_initial_stock_order(self, day_index):
        if day_index == 7:
            for p in PRODUCTS:
                new_order = {}
                new_order["product"] = p
                new_order["quantity"] = 10
                self.orders_for_factories.append(new_order)

    #storage cost = sum of stock for that day
    def calculate_storage_costs(self, day_index):
        total = 0
        for p in PRODUCTS:
            total += self.stock[p]
        self.cost_storage_per_day[day_index] += total

    def collect_all_demand_into_orders(self, day_index):
        for product, quantity in self.missed_wholesaler_orders.items():
            missed = quantity
            sold = self.sales_per_day[day_index-1][product]
            total_order = missed + sold
            
            if total_order > 0:
                self.orders_for_factories.append({"product": product, "quantity": total_order})
        
        self.missed_wholesaler_orders = {p: 0 for p in PRODUCTS}

    def send_orders_to_factories(self, factories, day_index):
        #we pass the parameter factories from the later Simulation so the distributor uses the shared factories.
        #keeping self.factories inside this class would create isolated copies, which is wrong.
        
        for order in self.orders_for_factories:
            target_factory = DISTRIBUTOR_PRODUCT_FACTORY[self.name][order["product"]]
            factories[target_factory].receive_order(self.name, order["product"], order["quantity"])
            self.cost_per_delivery_per_day[day_index][order["product"]] += 10 * LEAD_TIMES[self.name][target_factory]
        
        #reset orders list after sending
        self.orders_for_factories = []

    def receive_delivery(self, product, quantity, current_time, day_index, log_fn):
        self.stock[product] += quantity
        
        if self.name == "D1":
            log_fn(current_time)

    def calculate_total_costs_per_day(self, day_index):
        delivery_costs = sum(self.cost_per_delivery_per_day[day_index].values())
        storage_costs = self.cost_storage_per_day[day_index]
        
        self.total_cost_per_day[day_index] = delivery_costs + storage_costs


class Wholesalers:

    #wholesalers creates random orders during the day
    def create_order(self, distributors, current_time, day_index, log_fn):
        #we pass the parameter distributors from the later Simulation for the same reason as above with factories in the class distributor
        #keeping self.distributors inside this class would create isolated copies, which is wrong.

        distributors_list = list(distributors.values())
        #using a dict so we can access each distributor directly by its name (like "D1"),
        #makes everything easier to handle later in the simulation

        distributor = random.choice(distributors_list)
        product = random.choice(PRODUCTS)
        distributor.receive_wholesaler_order(product, current_time, day_index, log_fn)


class Simulation:
    def __init__(self):
        #initialize factories
        self.factories = {}
        for name in FACTORY_PRODUCTS:
            products = FACTORY_PRODUCTS[name]
            self.factories[name] = Factory(name, products)

        #initialize distributors
        self.distributors = {}
        for name in ["D1", "D2", "D3", "D4"]:
            self.distributors[name] = Distributor(name)

        #wholesaler object
        self.wholesalers = Wholesalers()

        #priority queue for events
        self.event_queue = []

        #current simulation time
        self.current_time = 0

        #logging for D1 only
        self.d1_stock_log = []

        #counter to generate unique event types
        self.event_counter = 0

        #used later for plotting
        self.time = []
        self.stock_per_time = []

    #log stock for D1 whenever a change happens
    def log_d1_stock(self, time_value):
        total_stock = 0
        for p in self.distributors["D1"].stock:
            total_stock += self.distributors["D1"].stock[p]

        self.d1_stock_log.append((time_value, total_stock))

        #avoid duplicates, keep latest only
        if len(self.time) == 0:
            self.time.append(time_value)
            self.stock_per_time.append(total_stock)
        else:
            if self.time[-1] != time_value:
                self.time.append(time_value)
                self.stock_per_time.append(total_stock)
            else:
                #replace last entry
                self.time[-1] = time_value
                self.stock_per_time[-1] = total_stock

    #push new event into queue
    def schedule_event(self, time_value, event_type, data):
        self.event_counter += 1
        new_type = event_type + "_" + str(self.event_counter)
        heapq.heappush(self.event_queue, (time_value, new_type, data))

    #schedule next product production for a factory
    def schedule_next_factory_production(self, factory_name, base_time):
        delta_seconds = random.expovariate(1 / 600)
        next_time = base_time + (delta_seconds / 3600.0)

        if next_time <= END_TIME:
            event_data = {"factory": factory_name}
            self.schedule_event(next_time, "factory_production", event_data)

    #schedule a delivery event
    def schedule_delivery(self, delivery_time, distributor, product, quantity):
        if delivery_time <= END_TIME:
            info = {}
            info["distributor"] = distributor
            info["product"] = product
            info["quantity"] = quantity
            self.schedule_event(delivery_time, "delivery", info)

    #schedule next wholesaler order event
    def schedule_next_wholesaler_order(self, base_time):
        delta_hours = random.uniform(600, 3600) / 3600.0
        next_time = base_time + delta_hours

        if next_time <= END_TIME:
            self.schedule_event(next_time, "wholesaler_order", {})

    #when a factory produces something
    def handle_factory_production(self, data):
        name = data["factory"]
        factory = self.factories[name]
        factory.produce_one_product()
        self.schedule_next_factory_production(name, self.current_time)

    #when a delivery arrives at a distributor
    def handle_delivery(self, data):
        distributor_name = data["distributor"]
        product = data["product"]
        quantity = data["quantity"]

        dist = self.distributors[distributor_name]

        day_index = int(self.current_time // 24)

        dist.receive_delivery(product, quantity, self.current_time, day_index, self.log_d1_stock)

    #when a wholesaler creates a random order
    def handle_wholesaler_order(self):
        day_index = int(self.current_time // 24)
        self.wholesalers.create_order(self.distributors, self.current_time, day_index, self.log_d1_stock)
        self.schedule_next_wholesaler_order(self.current_time)

    #daily event: cost calculation and sending orders
    def handle_daily_order_event(self, data):
        day = data["day"]

        #update stock log for plotting
        for dist in self.distributors.values():
            total_stock = 0
            for p in dist.stock:
                total_stock += dist.stock[p]
            dist.stock_total_per_day.append(total_stock)

        #storage costs
        for dist in self.distributors.values():
            dist.calculate_storage_costs(day)

        #initial stock order (day 7 only)
        if day == 7:
            for dist in self.distributors.values():
                dist.plan_initial_stock_order(day)
        else:
            #collect missed demand + sold stock
            for dist in self.distributors.values():
                dist.collect_all_demand_into_orders(day)

        #send orders to factories
        for dist in self.distributors.values():
            dist.send_orders_to_factories(self.factories, day)

        #add delivery + storage costs
        for dist in self.distributors.values():
            dist.calculate_total_costs_per_day(day)

        #factories attempt to fulfill pending orders
        for factory in self.factories.values():
            factory.process_orders(self.current_time, self.schedule_delivery)

    #prepare all starting events
    def first_events(self):
        #factory production events
        for name in self.factories:
            self.schedule_next_factory_production(name, 0)

        #daily events from day 7 to end
        for d in range(7, TOTAL_DAYS):
            info = {"day": d}
            self.schedule_event(d * 24, "daily_order", info)

        #first wholesaler order at day 8
        self.schedule_next_wholesaler_order(8 * 24)

        #initial stock logging
        self.log_d1_stock(0)

    #main loop
    def run(self):
        self.first_events()

        while len(self.event_queue) > 0:
            time_value, event_type, data = heapq.heappop(self.event_queue)

            if time_value > END_TIME:
                break

            self.current_time = time_value

            #strip unique suffix
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
    for i in range (100) :
        random.seed(i) 
        sim_i = Simulation()
        sim_i.run()

        d1 = sim_i.distributors["D1"]

        Ci = sum(d1.total_cost_per_day.values())
        Ni = sum(d1.sales_per_day[d] [p] for d in range(TOTAL_DAYS) for p in PRODUCTS)
        Ri = Ci/Ni

        C.append(Ci)
        N.append(Ni)
        R.append(Ri)
    
    print("Maximum Cost C:", max(C))
    print("Minimum Cost C:", min(C))
    print("Average Cost C:", sum(C)/len(C))
    print("Deviation Cost C:", np.std(C)) 
    print("\n")
    print("Maximum Number of Sales N:", max(N))
    print("Minimum Number of Sales N:", min(N))
    print("Average Number of Sales N:", sum(N)/len(N))
    print("Deviation Number of Sales N:", np.std(N))
    print("\n")
    print("Maximum Ratio R:", max(R))
    print("Minimum Ratio R:", min(R))
    print("Average Ratio R:", sum(R)/len(R))
    print("Deviation Ratio R:", np.std(R))
