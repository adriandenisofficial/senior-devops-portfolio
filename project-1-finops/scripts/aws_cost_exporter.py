import boto3
import time
import datetime
from botocore.exceptions import ClientError

# CONSTANTS
METRIC_FILE_PATH = "/home/ubuntu/senior-portfolio/project-1-finops/prom_metrics/cost.prom"

def get_real_aws_cost():
    """
    Fetches the actual unblended cost for the current month.
    Uses the IAM Role attached to the EC2 instance for authentication.
    """
    try:
        # Boto3 automatically uses the Instance Metadata Service to get credentials
        client = boto3.client('ce', region_name='us-east-1')

        # Define time period (Start of month to Today)
        now = datetime.datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        
        # If today is the 1st, use yesterday as end_date to avoid API errors
        if start_date == end_date:
             start_date = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        # The API Call
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )

        # Extract the dollar amount
        amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        return float(amount)

    except ClientError as e:
        print(f"AWS API Error: {e}")
        # FALLBACK: If API fails (e.g., Cost Explorer not enabled), return a dummy value
        # so the dashboard doesn't break during the demo.
        return 0.0
    except Exception as e:
        print(f"General Error: {e}")
        return 0.0

def write_to_prometheus(cost):
    """
    Writes the cost data to a file in Prometheus Text Format.
    Prometheus reads this file via the Textfile Collector.
    """
    content = f"""
# HELP aws_monthly_spend_total Total AWS spend for the current month
# TYPE aws_monthly_spend_total gauge
aws_monthly_spend_total {cost}
"""
    try:
        with open(METRIC_FILE_PATH, "w") as f:
            f.write(content)
        print(f"[{datetime.datetime.now()}] Updated Cost: ${cost}")
    except IOError as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    print("Starting Senior FinOps Exporter (IAM Role Authenticated)...")
    while True:
        cost = get_real_aws_cost()
        write_to_prometheus(cost)
        # AWS Cost Explorer updates once every 24 hours.
        # We check every 1 hour to stay fresh but save API calls.
        # For this demo, we sleep 60 seconds.
        time.sleep(60)
