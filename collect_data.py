"""
Main script to collect facility usage data periodically.
"""
import time
import schedule
from datetime import datetime
from scraper import FacilityUsageScraper
from database import FacilityDatabase


def collect_data():
    """Collect facility usage data and store it in the database."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collecting facility usage data...")
    
    scraper = FacilityUsageScraper(headless=True)
    db = FacilityDatabase()
    
    try:
        facilities = scraper.scrape()
        
        if facilities:
            print(f"Found {len(facilities)} facilities:")
            for facility in facilities:
                db.insert_usage_data(
                    facility_name=facility['name'],
                    timestamp=facility['timestamp'],
                    occupancy=facility.get('occupancy'),
                    capacity=facility.get('capacity'),
                    percentage=facility.get('percentage'),
                    metadata={'source': 'scraper'}
                )
                print(f"  - {facility['name']}: "
                      f"{facility.get('occupancy', 'N/A')}/{facility.get('capacity', 'N/A')} "
                      f"({facility.get('percentage', 'N/A'):.1f}%)")
        else:
            print("No facility data found. The page structure may have changed.")
    
    except Exception as e:
        print(f"Error collecting data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()


def main():
    """Main function to run the data collector."""
    print("CoRec Tracker - Data Collector")
    print("=" * 50)
    print("Collecting initial data...")
    
    # Collect data immediately
    collect_data()
    
    # Schedule data collection every 15 minutes
    schedule.every(15).minutes.do(collect_data)
    
    print("\nData collector running. Collecting data every 15 minutes.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nStopping data collector...")


if __name__ == "__main__":
    main()
