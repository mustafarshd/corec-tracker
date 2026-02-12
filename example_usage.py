"""
Example usage of the CoRec Tracker tool.
"""
from scraper import FacilityUsageScraper
from database import FacilityDatabase
from analyze import FacilityAnalyzer
from datetime import datetime, timedelta


def example_collect_once():
    """Example: Collect data once."""
    print("Example 1: Collecting data once")
    print("-" * 50)
    
    scraper = FacilityUsageScraper(headless=True)
    db = FacilityDatabase()
    
    try:
        facilities = scraper.scrape()
        for facility in facilities:
            db.insert_usage_data(
                facility_name=facility['name'],
                timestamp=facility['timestamp'],
                occupancy=facility.get('occupancy'),
                capacity=facility.get('capacity'),
                percentage=facility.get('percentage')
            )
            print(f"Saved: {facility['name']} - {facility.get('percentage', 'N/A'):.1f}%")
    finally:
        scraper.close()


def example_analyze():
    """Example: Analyze collected data."""
    print("\nExample 2: Analyzing collected data")
    print("-" * 50)
    
    analyzer = FacilityAnalyzer()
    
    # Get all facilities
    facilities = analyzer.db.get_all_facilities()
    
    if not facilities:
        print("No data found. Run collect_data.py first.")
        return
    
    # Analyze each facility
    for facility_name in facilities:
        best_times = analyzer.get_best_times(facility_name, days_back=7, top_n=3)
        
        if best_times:
            print(f"\n{facility_name}:")
            for slot in best_times:
                print(f"  Best: {slot['day']} at {slot['time']} "
                      f"({slot['avg_percentage']:.1f}% occupancy)")


def example_get_statistics():
    """Example: Get detailed statistics."""
    print("\nExample 3: Getting detailed statistics")
    print("-" * 50)
    
    analyzer = FacilityAnalyzer()
    facilities = analyzer.db.get_all_facilities()
    
    if not facilities:
        print("No data found.")
        return
    
    for facility_name in facilities[:1]:  # Just show first facility
        # Daily patterns
        daily = analyzer.get_daily_patterns(facility_name)
        print(f"\n{facility_name} - Average by Day:")
        for day, avg in sorted(daily.items(), key=lambda x: x[1]):
            print(f"  {day}: {avg:.1f}%")
        
        # Hourly patterns
        hourly = analyzer.get_hourly_patterns(facility_name)
        print(f"\n{facility_name} - Average by Hour:")
        for hour, avg in sorted(hourly.items(), key=lambda x: int(x[0])):
            print(f"  {hour}:00 - {avg:.1f}%")


if __name__ == "__main__":
    print("CoRec Tracker - Example Usage")
    print("=" * 50)
    
    # Run examples
    example_collect_once()
    example_analyze()
    example_get_statistics()
    
    print("\n" + "=" * 50)
    print("For continuous data collection, run: python collect_data.py")
    print("For detailed analysis, run: python analyze.py --facility <name>")
