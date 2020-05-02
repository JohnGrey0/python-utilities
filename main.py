import argparse
from helpers.generic_helper_methods import price_checker, tweet_speed_to_comcast

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pc', '--price_checker', action='store_true', help='Trigger the price checker')
    parser.add_argument('-st', '--speed_test', action='store_true', help='Trigger the speed test')
    args = parser.parse_args()
    
    if args.price_checker:
        price_checker()
    
    if args.speed_test:
        tweet_speed_to_comcast(platform='pi')
        
    