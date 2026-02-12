"""
Test script to verify the scraper is working correctly.
"""
from scraper import FacilityUsageScraper
from database import FacilityDatabase


def test_scraper():
    """Test the scraper functionality."""
    print("Testing Facility Usage Scraper")
    print("=" * 50)
    
    scraper = FacilityUsageScraper(headless=False)  # Show browser for debugging
    
    try:
        print("\n1. Testing scraper...")
        facilities = scraper.scrape()
        
        if facilities:
            print(f"\n[SUCCESS] Successfully scraped {len(facilities)} facilities:")
            for facility in facilities:
                print(f"  - {facility['name']}")
                if facility.get('occupancy') and facility.get('capacity'):
                    print(f"    Occupancy: {facility['occupancy']}/{facility['capacity']}")
                if facility.get('percentage'):
                    print(f"    Percentage: {facility['percentage']:.1f}%")
            
            print("\n2. Testing database storage...")
            db = FacilityDatabase()
            for facility in facilities:
                db.insert_usage_data(
                    facility_name=facility['name'],
                    timestamp=facility['timestamp'],
                    occupancy=facility.get('occupancy'),
                    capacity=facility.get('capacity'),
                    percentage=facility.get('percentage')
                )
            print("[SUCCESS] Data stored successfully")
            
            print("\n3. Testing data retrieval...")
            for facility in facilities:
                data = db.get_facility_data(facility['name'])
                print(f"  - {facility['name']}: {len(data)} data points")
            
            print("\n[SUCCESS] All tests passed!")
        else:
            print("\n[WARNING] No facilities found. This could mean:")
            print("  - The page structure has changed")
            print("  - The page requires authentication")
            print("  - The data is loaded dynamically and needs more time")
            print("\nCheck the browser window to see what's being loaded.")
    
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()
        print("\nTest complete.")


if __name__ == "__main__":
    test_scraper()
