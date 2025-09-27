import pandas as pd
from random import randint, choice
from datetime import datetime, timedelta

# Generate sample data
vendors = ["Vendor A", "Vendor B", "Vendor C", "Vendor D"]
descriptions = ["Office supplies", "Travel", "Subscription", "Misc"]

data = []
start_date = datetime(2025, 9, 1)

for i in range(20):  # 20 transactions
    date = start_date + timedelta(days=randint(0, 20))
    amount = choice([100, 250, 500, 1000, -150, -300])
    vendor = choice(vendors + ["Vendor A"])  # intentional duplicate
    description = choice(descriptions)
    data.append([date.strftime("%Y-%m-%d"), amount, vendor, description])

# Create DataFrame
df = pd.DataFrame(data, columns=["date", "amount", "vendor", "description"])

# Add an exact duplicate to test unmatched logic
df = pd.concat([df, df.iloc[2:3]], ignore_index=True)

# Save to Excel
sample_file_path = r"D:\sme_recon_mvp\uploads\sample_transactions.xlsx"

df.to_excel(sample_file_path, index=False)
print(f"Sample file created at: {sample_file_path}")
