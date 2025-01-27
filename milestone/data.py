import pandas as pd
import requests
import streamlit as st

# Load dataset
file_path = r"C:\Users\ADMIN\Downloads\Sugarcane_Supply_Chain_2021_2024.csv"
data = pd.read_csv(file_path)

# Inventory Management System with enhanced risk alerts
class InventoryManagementSystem:
    def __init__(self, locations, slack_webhook_url):
        self.slack_webhook_url = slack_webhook_url  # Slack webhook URL
        self.inventory = {
            location: {
                'warehouse_size': 0,  # Initialize later based on the dataset
                'available_space': 0,
                'materials': [],
                'total_cost': 0
            }
            for location in locations
        }

    def initialize_inventory(self):
        """Set initial warehouse size and available space from the dataset."""
        for _, row in data.iterrows():
            location = row['Location']
            warehouse_size = row['Storage Capacity (tons)']
            occupied_space = (row['Storage Occupied (%)'] / 100) * warehouse_size

            if location in self.inventory:
                self.inventory[location]['warehouse_size'] = warehouse_size
                self.inventory[location]['available_space'] = warehouse_size - occupied_space

    def send_slack_notification(self, message):
        """Sends a message to Slack using the webhook URL."""
        payload = {"text": message}
        response = requests.post(self.slack_webhook_url, json=payload)

        if response.status_code == 200:
            st.success("Slack notification sent successfully.")
        else:
            st.error(f"Failed to send Slack notification. Status code: {response.status_code}")

    def monthly_incoming(self, location, material_name, size, cost):
        """Handle the stocking of materials (incoming supplies from suppliers)."""
        if location not in self.inventory:
            st.error(f"Location '{location}' not found.")
            return

        if size > self.inventory[location]['available_space']:
            st.warning(f"Not enough space in the warehouse for location '{location}'. Risk: Stock Overflow.")
            return

        self.inventory[location]['materials'].append({'name': material_name, 'size': size, 'cost': cost})
        self.inventory[location]['available_space'] -= size
        self.inventory[location]['total_cost'] += cost
        st.success(
            f"Stocked up {material_name} in {location}. Available space: {self.inventory[location]['available_space']} tons.")

    def monthly_outgoing(self, location, material_name):
        """Handle the supply of materials (outgoing supplies to customers)."""
        if location not in self.inventory:
            st.error(f"Location '{location}' not found.")
            return

        material_found = False
        for material in self.inventory[location]['materials']:
            if material['name'] == material_name:
                self.inventory[location]['available_space'] += material['size']
                self.inventory[location]['total_cost'] -= material['cost']
                self.inventory[location]['materials'].remove(material)
                material_found = True
                st.success(
                    f"Supplied {material_name} from {location}. Available space: {self.inventory[location]['available_space']} tons.")
                break

        if not material_found:
            st.error(f"Material '{material_name}' not found in location '{location}'.")

    def display_inventory(self, location):
        """Display the current inventory status for a specific location."""
        if location not in self.inventory:
            st.error(f"Location '{location}' not found.")
            return

        st.write(f"### Location: {location}")
        st.write(f"  Warehouse Size: {self.inventory[location]['warehouse_size']} tons")
        st.write(f"  Available Space: {self.inventory[location]['available_space']} tons")
        st.write(f"  Materials:")
        for material in self.inventory[location]['materials']:
            st.write(f"    - {material['name']}: Size={material['size']} tons, Cost=${material['cost']}")
        st.write(f"  Total Cost of Materials: ${self.inventory[location]['total_cost']}")
        st.write("-" * 40)

    def generate_risk_alerts(self):
        """Generate alerts for supply chain risks based on storage and export volume."""
        st.write("### Generating Risk Alerts:")
        for _, row in data.iterrows():
            location = row['Location']
            export_volume = row['Export Volume (tons)']
            weather_conditions = row['Weather Conditions']

            available_space = self.inventory[location]['available_space']
            warehouse_size = self.inventory[location]['warehouse_size']

            alert_message = f"Location: {location}\nExport Volume: {export_volume} tons\nWeather: {weather_conditions}\n"

            # Generate capacity-based alerts
            if available_space <= 0.1 * warehouse_size and available_space > 0:
                alert_message += f"⚠️ Alert: Stock Shortage! Critical space available in {location}."
            elif available_space == 0:
                alert_message += f"🚨 Alert: High Risk! Warehouse in {location} is empty. Immediate restocking required."
            elif available_space < 0:
                alert_message += f"⚠️ Alert: Stock Overflow! Exceeded space capacity in {location}."
            elif available_space == warehouse_size:
                alert_message += f"⚠️ Risk: Empty warehouse in {location}. No stock available!"

            # Send the alert to Slack
            self.send_slack_notification(alert_message)

            st.write(alert_message)
            st.write("-" * 40)

    def save_inventory_to_csv(self):
        """Save the current inventory status to a CSV file."""
        inventory_data = []
        for location, details in self.inventory.items():
            for material in details['materials']:
                inventory_data.append({
                    'Location': location,
                    'Material Name': material['name'],
                    'Size (tons)': material['size'],
                    'Cost ($)': material['cost'],
                    'Available Space (tons)': details['available_space'],
                    'Total Cost ($)': details['total_cost']
                })

        df = pd.DataFrame(inventory_data)
        df.to_csv('inventory_status.csv', index=False)
        st.success("Inventory saved to 'inventory_status.csv'.")


# Streamlit App

slack_webhook_url = "https://hooks.slack.com/services/your-slack-webhook"  # Replace with your Slack webhook URL
locations = data['Location'].unique()  # Extract locations from dataset
ims = InventoryManagementSystem(locations=locations, slack_webhook_url=slack_webhook_url)
ims.initialize_inventory()

st.title("Inventory Management System")

# Select Location
location = st.selectbox("Select Location", locations)

# Actions
action = st.selectbox("Select Action",
                      ["Monthly Incoming", "Monthly Outgoing", "Display Inventory", "Generate Risk Alerts",
                       "Save and Exit"])

if action == "Monthly Incoming":
    material_name = st.text_input("Material Name")
    size = st.number_input("Material Size (in tons)", min_value=0.0)
    cost = st.number_input("Material Cost", min_value=0.0)

    if st.button("Submit Incoming Stock"):
        ims.monthly_incoming(location, material_name, size, cost)

elif action == "Monthly Outgoing":
    material_name = st.text_input("Material Name to Supply")

    if st.button("Submit Outgoing Stock"):
        ims.monthly_outgoing(location, material_name)

elif action == "Display Inventory":
    ims.display_inventory(location)

elif action == "Generate Risk Alerts":
    if st.button("Generate Alerts"):
        ims.generate_risk_alerts()

elif action == "Save and Exit":
    ims.save_inventory_to_csv()
    st.success("Exiting the system.")
