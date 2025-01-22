
import mysql.connector
import pandas as pd

# Connect to MySQL database (update the credentials as needed)
conn = mysql.connector.connect(
    host="127.0.0.1",  # For example: "localhost" or IP address
    user="system",       # Your MySQL username
    password="manager",  # Your MySQL password
    database="inventory_management"  # Database name
)
cursor = conn.cursor()

# Create tables if they don't exist, including "Published At" for adjustments
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    country_name VARCHAR(255) PRIMARY KEY,
    stock_level INT,
    threshold INT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS risk_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    risk_level VARCHAR(50),
    stock_adjustment FLOAT,
    `Published At` DATE
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS adjusted_inventory (
    country_name VARCHAR(255) PRIMARY KEY,
    stock_level INT,
    stock_adjusted INT,
    adjustment FLOAT,
    `Published At` DATE
)
""")

# Insert mock data into inventory table (only once), now using country names
mock_inventory = [
    
('Bolivia', 500, 100),
('Brazil', 1000, 200),
('China', 600, 120),
('Colombia', 500, 100),
('Ethiopia', 700, 180),
('India', 1200, 250),
('Indonesia', 900, 200),
('Italy', 450, 90),
('Korea', 300, 60),
('Peru', 400, 80),
('Russia', 500, 100),
('Vietnam', 800, 150)
]

cursor.executemany("""
INSERT IGNORE INTO inventory (country_name, stock_level, threshold)
VALUES (%s, %s, %s)
""", mock_inventory)
conn.commit()

# Load risk data from the provided CSV file without renaming 'Published At'
risk_data_path = "sentiment_and_risk_analysis_results.csv"
risk_data = pd.read_csv(risk_data_path)

# Ensure 'Published At' remains as is, and parse it as a date
risk_data['Published At'] = pd.to_datetime(risk_data['Published At']).dt.date

# Adjust stock based on risk levels (considering the latest "Published At" date)
def adjust_stock_db(title, risk_level, published_at):
    for country in mock_inventory:
        if country[0].lower() in title.lower():
            # Fetch stock level
            cursor.execute("SELECT stock_level FROM inventory WHERE country_name = %s", (country[0],))
            stock_level = cursor.fetchone()[0]

            # Adjust stock
            if risk_level == 'High':
                stock_adjustment = stock_level * -0.20  # Decrease by 20%
            elif risk_level == 'Medium':
                stock_adjustment = stock_level * 0.0  # No change
            elif risk_level == 'Low':
                stock_adjustment = stock_level * 0.05  # Increase by 5%
            else:
                stock_adjustment = 0

            # Calculate the new stock level after adjustment
            new_stock = int(stock_level + stock_adjustment)

            # Check if the country already has an adjustment in adjusted_inventory
            cursor.execute("""
                SELECT `Published At` FROM adjusted_inventory 
                WHERE country_name = %s
            """, (country[0],))
            result = cursor.fetchone()

            # Insert or update based on the Published At date
            if result:
                existing_date = result[0]
                if published_at > existing_date:
                    # Update the existing entry if the new date is later
                    cursor.execute("""
                        UPDATE adjusted_inventory
                        SET stock_level = %s, stock_adjusted = %s, adjustment = %s, `Published At` = %s
                        WHERE country_name = %s
                    """, (stock_level, new_stock, stock_adjustment, published_at, country[0]))
            else:
                # Insert a new entry if no existing record
                cursor.execute("""
                    INSERT INTO adjusted_inventory (country_name, stock_level, stock_adjusted, adjustment, `Published At`)
                    VALUES (%s, %s, %s, %s, %s)
                """, (country[0], stock_level, new_stock, stock_adjustment, published_at))
            conn.commit()

            return stock_adjustment

# Apply adjustments and store risk data in the database
for _, row in risk_data.iterrows():
    adjustment = adjust_stock_db(row['Title'], row['Risk Level'], row['Published At'])
    cursor.execute("""
        INSERT INTO risk_data (title, risk_level, stock_adjustment, `Published At`)
        VALUES (%s, %s, %s, %s)
    """, (row['Title'], row['Risk Level'], adjustment, row['Published At']))
conn.commit()

# Fetch updated adjusted inventory for review
cursor.execute("SELECT * FROM adjusted_inventory")
updated_adjusted_inventory = cursor.fetchall()

# Display the adjusted inventory
print(pd.DataFrame(updated_adjusted_inventory, columns=["Country", "Stock Level", "Stock Adjusted", "Adjustment", "Published At"]))

# Close the database connection
conn.close()

