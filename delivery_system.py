import json
import math
from typing import Dict, List, Any
import os


class DeliverySystemSimulator:
    # Simulates delivery operations for multiple agents and packages.
    
    def __init__(self, data_file: str):

        # Initialize simulator with JSON data file.
        # Args: data_file (str): Path to input JSON file containing warehouses, agents, packages
        
        self.data_file = data_file
        self.warehouses = {}
        self.agents = {}
        self.packages = []
        self.package_assignments = {}
        self.agent_stats = {}
        
    def load_data(self) -> bool:

        # Load and parse JSON data file.
        # Handles both formats:
        # - Format 1: warehouses/agents as dicts with ID->location mapping
        # - Format 2: warehouses/agents as lists with {id, location} objects
        # Returns: bool: True if successful, False otherwise

        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Handle warehouses - both dict and list formats
            
            if isinstance(data.get('warehouses'), dict):
                self.warehouses = data['warehouses']
            elif isinstance(data.get('warehouses'), list):
                self.warehouses = {wh['id']: wh['location'] for wh in data['warehouses']}
            else:
                return False
                
            # Handle agents - both dict and list formats
            if isinstance(data.get('agents'), dict):
                self.agents = data['agents']
            elif isinstance(data.get('agents'), list):
                self.agents = {ag['id']: ag['location'] for ag in data['agents']}
            else:
                return False
                
            if isinstance(data.get('packages'), list):
                self.packages = data['packages']
            else:
                return False
                
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    @staticmethod
    def euclidean_distance(point1: List[float], point2: List[float]) -> float:
        # Calculate Euclidean distance between two points.
        # Formula: d = sqrt((x2-x1)^2 + (y2-y1)^2)
        return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
    
    def find_nearest_agent(self, warehouse_location: List[float]) -> str:
        # Find the agent nearest to a warehouse.
        nearest_agent = None
        min_distance = float('inf')
        
        for agent_id, agent_location in self.agents.items():
            distance = self.euclidean_distance(agent_location, warehouse_location)
            if distance < min_distance:
                min_distance = distance
                nearest_agent = agent_id
        
        return nearest_agent
    
    def assign_packages_to_agents(self):
        # Assign each package to the nearest agent.
        # Handles both "warehouse" and "warehouse_id" keys.
        for package in self.packages:
            package_id = package['id']
            warehouse_id = package.get('warehouse') or package.get('warehouse_id')
            warehouse_location = self.warehouses[warehouse_id]
            nearest_agent = self.find_nearest_agent(warehouse_location)
            self.package_assignments[package_id] = nearest_agent
    
    def simulate_delivery(self):
        # Simulate delivery for all packages.
        # Calculate total distance and delivery count for each agent.
        for agent_id in self.agents.keys():
            self.agent_stats[agent_id] = {
                'packages_delivered': 0,
                'total_distance': 0.0,
                'efficiency': 0.0,
                'packages': []
            }
        
        for package in self.packages:
            package_id = package['id']
            warehouse_id = package.get('warehouse') or package.get('warehouse_id')
            destination = package['destination']
            
            agent_id = self.package_assignments[package_id]
            agent_location = self.agents[agent_id]
            warehouse_location = self.warehouses[warehouse_id]
            
            # Calculate distances
            agent_to_warehouse = self.euclidean_distance(agent_location, warehouse_location)
            warehouse_to_destination = self.euclidean_distance(warehouse_location, destination)
            total_distance_for_package = agent_to_warehouse + warehouse_to_destination
            
            # Update agent stats
            self.agent_stats[agent_id]['packages_delivered'] += 1
            self.agent_stats[agent_id]['total_distance'] += total_distance_for_package
            self.agent_stats[agent_id]['packages'].append({
                'package_id': package_id,
                'warehouse': warehouse_id,
                'distance': total_distance_for_package
            })
        
        # Calculate efficiency
        for agent_id, stats in self.agent_stats.items():
            if stats['packages_delivered'] > 0:
                stats['efficiency'] = stats['total_distance'] / stats['packages_delivered']
            else:
                stats['efficiency'] = 0.0
    
    def find_best_agent(self) -> str:
        # Determine the most efficient agent.
        # Best agent has lowest efficiency (least distance per package).
        best_agent = None
        best_efficiency = float('inf')
        best_packages = 0
        
        for agent_id, stats in self.agent_stats.items():
            if stats['packages_delivered'] > 0:
                efficiency = stats['efficiency']
                packages_delivered = stats['packages_delivered']
                
                if efficiency < best_efficiency or \
                   (efficiency == best_efficiency and packages_delivered > best_packages):
                    best_efficiency = efficiency
                    best_agent = agent_id
                    best_packages = packages_delivered
        
        return best_agent if best_agent else "N/A"
    
    def generate_report(self) -> Dict[str, Any]:
        # Generate delivery report.
        report = {}
        
        for agent_id, stats in self.agent_stats.items():
            report[agent_id] = {
                'packages_delivered': stats['packages_delivered'],
                'total_distance': round(stats['total_distance'], 2),
                'efficiency': round(stats['efficiency'], 2)
            }
        
        report['best_agent'] = self.find_best_agent()
        return report
    
    def save_report(self, output_file: str):
        # Save report to JSON file.
        report = self.generate_report()
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[OK] Report saved: {output_file}")
    
    def run_simulation(self, output_file: str = None) -> Dict[str, Any]:
        # Run complete simulation pipeline.
        if not self.load_data():
            return None
        
        print(f"  [OK] Warehouses: {len(self.warehouses)}, Agents: {len(self.agents)}, Packages: {len(self.packages)}")
        
        self.assign_packages_to_agents()
        self.simulate_delivery()
        report = self.generate_report()
        
        if output_file:
            self.save_report(output_file)
        
        return report


def print_report(report: Dict[str, Any], input_file: str):
    # Print formatted report.
    print(f"\n{'='*60}")
    print(f"REPORT: {input_file}")
    print(f"{'='*60}")
    
    for agent_id in sorted([k for k in report.keys() if k != 'best_agent']):
        stats = report[agent_id]
        print(f"{agent_id}: {stats['packages_delivered']} pkg, {stats['total_distance']:.2f} units, {stats['efficiency']:.2f} eff")
    
    best = report['best_agent']
    if best != "N/A":
        print(f"[BEST] {best}")
    print()


if __name__ == "__main__":
    print("FastBox Delivery System Simulator\n")
    
    # Base case
    base_case_file = "base_case.json"
    if os.path.exists(base_case_file):
        print(f"[1/2] {base_case_file}")
        simulator = DeliverySystemSimulator(base_case_file)
        report = simulator.run_simulation(output_file="report.json")
        if report:
            print_report(report, base_case_file)
    
    # Test cases
    test_cases_dir = "Python Assignment(Delivery System Test Cases)"
    if os.path.exists(test_cases_dir):
        print(f"\n[2/2] Test cases from {test_cases_dir}\n")
        
        test_files = sorted([f for f in os.listdir(test_cases_dir) 
                           if f.startswith('test_case_') and f.endswith('.json')])
        
        for i, test_file in enumerate(test_files, 1):
            test_path = os.path.join(test_cases_dir, test_file)
            output_file = os.path.join(test_cases_dir, f"report_{test_file.replace('.json', '')}.json")
            
            print(f"  [{i}/{len(test_files)}] {test_file}")
            simulator = DeliverySystemSimulator(test_path)
            report = simulator.run_simulation(output_file=output_file)
            if report:
                print_report(report, test_file)
    
    print("[OK] All simulations completed!")
