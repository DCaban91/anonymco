import argparse
import csv
import pendulum
from tabulate import tabulate
from importlib.resources import read_binary

def main():
    parser = argparse.ArgumentParser(description='Anonymco tech screen')
    parser.add_argument('-ad', help='Ad exposure data csv file')
    parser.add_argument('-sd', help='Sales data from advertiser csv file')

    args = parser.parse_args()
    
    # TODO: validate input
    ad_exposure_data = {}
    sd_data = {}
    creative_stats = {}

    # Parse the ad exposure data and store the information based on the user_id in memory
    with open(args.ad) as ad_csv_file:
        fieldnames = ['user_id', 'timestamp', 'creative_id']
        reader = csv.DictReader(ad_csv_file, fieldnames=fieldnames)
        for row in reader:
            # Skip the header row if it's set
            if row[fieldnames[0]] == fieldnames[0]:
                continue
            user_id = row[fieldnames[0]]
            time_stamp = pendulum.from_format(row[fieldnames[1]], fmt='YYYY-MM-DD HH:mm:ss') 
            creative_id = row[fieldnames[2]]

            # Add the userId to the dictionary if it doesn't exist
            if user_id not in ad_exposure_data:
                ad_exposure_data[user_id] = []
            
            # Add the ad exposure information for the user to the list
            ad_exposure_data[user_id].append({fieldnames[1]: time_stamp, fieldnames[2]: creative_id})

            if creative_id not in creative_stats:
                creative_stats[creative_id] = {'dimension': 'creative_id', 'value': creative_id, 'num_purchasers': 0, 'total_sales': 0}

    # Parse the sale data and store the information based on the user_id in memory
    with open(args.sd) as sd_csv_file:
        fieldnames = ['user_id', 'timestamp', 'amount']
        reader = csv.DictReader(sd_csv_file, fieldnames=fieldnames)
        for row in reader:
            # Skip the header row if it's set
            if row[fieldnames[0]] == fieldnames[0]:
                continue
            user_id = row[fieldnames[0]]
            time_stamp = pendulum.from_format(row[fieldnames[1]], fmt='YYYY-MM-DD HH:mm:ss') 
            amount = float(row[fieldnames[2]])

            # Add the userId to the dictionary if it doesn't exist
            if user_id not in sd_data:
                sd_data[user_id] = []
            
            # Add the sales data for the user to the list
            sd_data[user_id].append({fieldnames[1]: time_stamp, fieldnames[2]: amount})

    overall_unique_customers = 0
    overall_total_sales = 0
    user_credit_tracking = []
    # n^3 in complexity which isn't good. Should look into optimizing this code
    for user_id, sales_data in sd_data.items():
        # User made a purchase without being exposed to an ad, sum up the sales and move on to the next user
        if user_id not in ad_exposure_data:
            continue
        sorted_exposure_data = sorted(ad_exposure_data[user_id], key=lambda d: d['timestamp'])
        ad_credit_tracking = [] 
        for sale_data in sales_data:
            sale_timestamp = sale_data['timestamp']
            ad_credit = None
            for exposure_data in sorted_exposure_data:
                if exposure_data['timestamp'] < sale_timestamp:
                    ad_credit = exposure_data
                else:
                    # Short circuit out of the loop as we've gone through all the possible exposure data this sale could be attributed to
                    break
            # Give the ad credit for the sale if we have one to give credit to
            if ad_credit:
                creative_stats[ad_credit['creative_id']]['total_sales'] += sale_data['amount']
                overall_total_sales += sale_data['amount']
                if ad_credit not in ad_credit_tracking:
                    creative_stats[ad_credit['creative_id']]['num_purchasers'] += 1
                    ad_credit_tracking.append(ad_credit)
                    if user_id not in user_credit_tracking:
                        overall_unique_customers += 1
                        user_credit_tracking.append(user_id)

    # Write out the results
    pre_pended_dict = [{'dimension': 'overall', 'value': 'overall', 'num_purchasers': overall_unique_customers, 'total_sales': overall_total_sales}]
    for item in creative_stats.values():
        pre_pended_dict.append(item)
    
    print(tabulate(pre_pended_dict, headers="keys", floatfmt=".2f"))

    print("Done")
if __name__ == "__main__":
    main()