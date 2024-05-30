# public_transport_payoff.py

import numpy as np
import pandas as pd
import math
import networkx as nx

# Parameters for the network
TIME_INTERVALS = 48
NODES = 25
ticket_price = 3
operation_hours = 18
routes = {
    'Route1': [1, 5, 6, 7, 12, 15, 16, 17, 18, 20, 21, 14, 10, 9, 3, 2, 1],
    'Route2': [1, 2, 3, 9, 10, 14, 21, 20, 18, 17, 16, 15, 12, 7, 6, 5, 1],
    'Route3': [25, 24, 23, 22, 14, 19, 13, 8, 4, 5, 4, 8, 13, 19, 14, 22, 23, 24, 25],
    'Route4': [16, 12, 11, 7, 4, 3, 4, 7, 11, 12, 16]
}
bus_cost = 450000 * 0.1845
charging_fix_cost = 100000 * 0.1845
charging_pile_cost = 1000 * 0.1845
average_electricity_price_per_KWh = 0.20134
KWh_cost_per_km = 446 / 350
charging_KWh_per_time_interval = 45
unit_charging_cost = average_electricity_price_per_KWh * KWh_cost_per_km
unit_operation_cost = 30
speed = 10
charging_speed = charging_KWh_per_time_interval / KWh_cost_per_km
C = 70
n = 365

delta = 0.001 # CO2 emission coefficient

file_path = 'distance.xlsx'
xl = pd.read_excel(file_path, header=None)
d = xl.values

def initialize_graph(routes, d):
    graph = nx.DiGraph()
    routes_at_stop = {}
    
    for route_id, stops in routes.items():
        for stop in stops:
            if stop not in routes_at_stop:
                routes_at_stop[stop] = set()
            routes_at_stop[stop].add(route_id)
    
    for route_id, stops in routes.items():
        for i in range(len(stops) - 1):
            stop1, stop2 = stops[i], stops[i + 1]
            graph.add_edge(stop1, stop2, weight=d[stop1-1, stop2-1])
    
    return graph

def calculate_traffic_burden(graph, D, time_intervals, speed):
    NODES = D.shape[1]
    F_tij = np.zeros((time_intervals, NODES, NODES))
    for t in range(time_intervals):
        for i in range(NODES):
            for j in range(NODES):
                if i != j:
                    path = nx.shortest_path(graph, i+1, j+1, weight='weight')
                    for k in range(len(path) - 1):
                        current_time = (t + math.floor(nx.shortest_path_length(graph, i+1, path[k+1], weight='weight')/speed)) % time_intervals
                        start, end = path[k], path[k + 1]
                        F_tij[current_time, start-1, end-1] += D[t, i, j]
    return F_tij

def calculate_departing_buses(F_tij, routes, d, bus_capacity, time_intervals, speed):
    departing_buses = {route_id: np.zeros(time_intervals) for route_id in routes}
    
    for t in range(time_intervals):
        for route_id, stops in routes.items():
            demand = np.zeros(len(stops)-1)
            for i in range(len(stops) - 1):
                start, end = stops[i], stops[i + 1]
                travel_time = math.floor(d[stops[0]-1, end-1]/speed)
                demand[i] = F_tij[(t + travel_time)%time_intervals, start-1, end-1]
            departing_buses[route_id][t] = math.ceil(np.max(demand) / bus_capacity)
    
    return departing_buses

def max_buses_on_trip(timetable, trip_time, time_intervals):
    buses_on_trip = np.zeros(time_intervals)
    for t in range(time_intervals):
        if timetable[t] > 0:
            start_trip = t
            end_trip = t + trip_time
            if end_trip < time_intervals:
                buses_on_trip[start_trip:end_trip] += timetable[t]
            else:
                buses_on_trip[start_trip:] += timetable[t]
    return np.max(buses_on_trip)

def max_buses_charging(timetable, trip_time, charging_time, time_intervals):
    buses_charging = np.zeros(time_intervals)
    for t in range(time_intervals):
        end_trip = t + trip_time
        if end_trip < time_intervals and timetable[t] > 0:
            start_charging = end_trip
            end_charging = end_trip + charging_time
            if end_charging < time_intervals:
                buses_charging[start_charging:end_charging] += timetable[t]
            else:
                buses_charging[start_charging:] += timetable[t]
    return np.max(buses_charging)

def calculate_fleet_size(departing_buses, routes, d, speed, charging_speed, time_intervals):
    buses_needed = np.zeros(len(routes))
    buses_charging = np.zeros(len(routes))
    for j, (route_id, timetable) in enumerate(departing_buses.items()):
        stops = routes[route_id]
        route_length = sum([d[stops[i]-1, stops[i+1]-1] for i in range(len(stops) - 1)])
        trip_time = math.ceil(route_length/speed)
        charging_time = math.ceil(route_length/charging_speed)
        trip = max_buses_on_trip(timetable, trip_time, time_intervals)
        charging = max_buses_charging(timetable, trip_time, charging_time, time_intervals)
        buses_needed[j] = trip + charging
        buses_charging[j] = charging
    return buses_needed, buses_charging

def calculate_route_length(departing_buses, routes, d):
    route_travel_distance = np.zeros(len(routes))
    for j, (route_id, timetable) in enumerate(departing_buses.items()):
        stops = routes[route_id]
        route_length = sum([d[stops[i]-1, stops[i+1]-1] for i in range(len(stops) - 1)])
        route_travel_distance[j] = sum(timetable) * route_length
    return route_travel_distance

def calculate_payoff(demand_file):
    # Load the demand data D from Excel file
    xl = pd.ExcelFile(demand_file)
    D = np.empty((len(xl.sheet_names), NODES, NODES))
    for i, sheet in enumerate(xl.sheet_names):
        D[i] = xl.parse(sheet, header=None).values

    graph = initialize_graph(routes, d)
    F_tij = calculate_traffic_burden(graph, D, TIME_INTERVALS, speed)
    departing_buses = calculate_departing_buses(F_tij, routes, d, C, TIME_INTERVALS, speed)
    U_ticket = np.sum(D) * ticket_price * n
    fleet_size, charging_fleet_size = calculate_fleet_size(departing_buses, routes, d, speed, charging_speed, TIME_INTERVALS)
    fleet_investment_cost = bus_cost * sum(fleet_size)
    charging_station_cost = 3 * charging_fix_cost + charging_pile_cost * sum(charging_fleet_size)
    total_travel_distance = sum(calculate_route_length(departing_buses, routes, d))
    charging_cost = total_travel_distance * unit_charging_cost * n
    operation_cost = sum(fleet_size) * operation_hours * unit_operation_cost * n
    Payoff = U_ticket - fleet_investment_cost - charging_station_cost - charging_cost - operation_cost
    infrastructure_cost = fleet_investment_cost + charging_station_cost
    variable_cost = charging_cost + operation_cost
    return Payoff, infrastructure_cost, variable_cost

def gov_env(saev_demand_file,pt_demand_file):

    xl = pd.ExcelFile(saev_demand_file)
    D_SAEV = np.empty((len(xl.sheet_names), NODES, NODES))
    for i, sheet in enumerate(xl.sheet_names):
        D_SAEV[i] = xl.parse(sheet, header=None).values

    xl = pd.ExcelFile(pt_demand_file)
    D_PT = np.empty((len(xl.sheet_names), NODES, NODES))
    for i, sheet in enumerate(xl.sheet_names):
        D_PT[i] = xl.parse(sheet, header=None).values   
    
    payoff = 0

    for i in range(NODES):
        for j in range(NODES):
            for t in range(TIME_INTERVALS):
                payoff -= 367.3*delta*d[i,j]*D_SAEV[t,i,j] + 572.3*delta*d[i,j]*math.ceil(D_PT[t,i,j]/C)
    
    return payoff


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python public_transport_payoff.py <demand_data_file.xlsx>")
        sys.exit(1)
    demand_file = sys.argv[1]
    Payoff, infrastructure_cost, variable_cost = calculate_payoff(demand_file)
    print("Payoff:", Payoff, "Infrastructure Cost:", infrastructure_cost, "Variable Cost:", variable_cost)
