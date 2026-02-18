"""
Analysis tool to recommend the best times to visit facilities.
"""
import argparse
from datetime import datetime, timedelta
from typing import List, Dict
from database import FacilityDatabase
import pandas as pd


class FacilityAnalyzer:
    def __init__(self, db_path: str = "facility_data.db"):
        self.db = FacilityDatabase(db_path)
    
    def get_best_times(self, facility_name: str, days_back: int = 7, 
                      top_n: int = 5) -> list[dict]:
        """
        Get the best times to visit a facility based on historical data.
        
        Args:
            facility_name: Name of the facility
            days_back: Number of days to analyze (default: 7)
            top_n: Number of best time slots to return (default: 5)
        
        Returns:
            List of dictionaries with best time slots
        """
        # Get aggregated data by time of day
        data = self.db.get_data_by_time_of_day(facility_name, days_back)
        
        if not data:
            return []
        
        # Flatten and sort by average percentage (lower is better)
        time_slots = []
        for day, times in data.items():
            for time_str, stats in times.items():
                if stats['sample_count'] > 0:  # Only include times with data
                    time_slots.append({
                        'day': day,
                        'time': time_str,
                        'avg_percentage': stats['avg_percentage'],
                        'avg_occupancy': stats['avg_occupancy'],
                        'sample_count': stats['sample_count']
                    })
        
        # Sort by average percentage (ascending - lower occupancy is better)
        time_slots.sort(key=lambda x: x['avg_percentage'] or float('inf'))
        
        return time_slots[:top_n]
    
    def get_worst_times(self, facility_name: str, days_back: int = 7, 
                       top_n: int = 5) -> list[dict]:
        """Get the worst (busiest) times to visit a facility."""
        data = self.db.get_data_by_time_of_day(facility_name, days_back)
        
        if not data:
            return []
        
        time_slots = []
        for day, times in data.items():
            for time_str, stats in times.items():
                if stats['sample_count'] > 0:
                    time_slots.append({
                        'day': day,
                        'time': time_str,
                        'avg_percentage': stats['avg_percentage'],
                        'avg_occupancy': stats['avg_occupancy'],
                        'sample_count': stats['sample_count']
                    })
        
        # Sort by average percentage (descending - higher occupancy is worse)
        time_slots.sort(key=lambda x: x['avg_percentage'] or 0, reverse=True)
        
        return time_slots[:top_n]
    
    def get_daily_patterns(self, facility_name: str, days_back: int = 7) -> Dict:
        """Get average occupancy patterns by day of week."""
        data = self.db.get_data_by_time_of_day(facility_name, days_back)
        
        if not data:
            return {}
        
        daily_averages = {}
        for day, times in data.items():
            percentages = [stats['avg_percentage'] 
                          for stats in times.values() 
                          if stats['avg_percentage'] is not None]
            if percentages:
                daily_averages[day] = sum(percentages) / len(percentages)
        
        return daily_averages
    
    def get_hourly_patterns(self, facility_name: str, days_back: int = 7) -> Dict:
        """Get average occupancy patterns by hour of day."""
        data = self.db.get_data_by_time_of_day(facility_name, days_back)
        
        if not data:
            return {}
        
        hourly_averages = {}
        for day, times in data.items():
            for time_str, stats in times.items():
                hour = time_str.split(':')[0]
                if hour not in hourly_averages:
                    hourly_averages[hour] = []
                if stats['avg_percentage'] is not None:
                    hourly_averages[hour].append(stats['avg_percentage'])
        
        # Calculate average for each hour
        hourly_avg = {}
        for hour, percentages in hourly_averages.items():
            if percentages:
                hourly_avg[hour] = sum(percentages) / len(percentages)
        
        return hourly_avg
    
    def print_recommendations(self, facility_name: str, days_back: int = 7):
        """Print formatted recommendations for a facility."""
        print(f"\n{'='*60}")
        print(f"Recommendations for: {facility_name}")
        print(f"Based on data from the last {days_back} days")
        print(f"{'='*60}\n")
        
        # Check if we have data
        all_data = self.db.get_facility_data(facility_name)
        if not all_data:
            print(f"No data found for {facility_name}.")
            print("Make sure to run collect_data.py first to gather data.")
            return
        
        print(f"Total data points collected: {len(all_data)}\n")
        
        # Best times
        best_times = self.get_best_times(facility_name, days_back)
        if best_times:
            print("BEST TIMES TO VISIT (Lowest Occupancy):")
            print("-" * 60)
            for i, slot in enumerate(best_times, 1):
                pct = slot['avg_percentage']
                occ = slot['avg_occupancy']
                samples = slot['sample_count']
                print(f"{i}. {slot['day']} at {slot['time']}")
                print(f"   Average Occupancy: {pct:.1f}% "
                      f"({occ:.0f} people)" if occ else f"({pct:.1f}%)")
                print(f"   Based on {samples} samples")
            print()
        
        # Worst times
        worst_times = self.get_worst_times(facility_name, days_back)
        if worst_times:
            print("WORST TIMES TO VISIT (Highest Occupancy):")
            print("-" * 60)
            for i, slot in enumerate(worst_times, 1):
                pct = slot['avg_percentage']
                occ = slot['avg_occupancy']
                samples = slot['sample_count']
                print(f"{i}. {slot['day']} at {slot['time']}")
                print(f"   Average Occupancy: {pct:.1f}% "
                      f"({occ:.0f} people)" if occ else f"({pct:.1f}%)")
                print(f"   Based on {samples} samples")
            print()
        
        # Daily patterns
        daily_patterns = self.get_daily_patterns(facility_name, days_back)
        if daily_patterns:
            print("AVERAGE OCCUPANCY BY DAY OF WEEK:")
            print("-" * 60)
            sorted_days = sorted(daily_patterns.items(), 
                               key=lambda x: x[1])
            for day, avg_pct in sorted_days:
                bar_length = int(avg_pct / 2)  # Scale for display
                bar = "#" * bar_length + "-" * (50 - bar_length)
                print(f"{day:12} {bar} {avg_pct:.1f}%")
            print()
        
        # Hourly patterns
        hourly_patterns = self.get_hourly_patterns(facility_name, days_back)
        if hourly_patterns:
            print("AVERAGE OCCUPANCY BY HOUR:")
            print("-" * 60)
            sorted_hours = sorted(hourly_patterns.items(), key=lambda x: int(x[0]))
            for hour, avg_pct in sorted_hours:
                bar_length = int(avg_pct / 2)
                bar = "#" * bar_length + "-" * (50 - bar_length)
                time_str = f"{int(hour):02d}:00"
                print(f"{time_str:6} {bar} {avg_pct:.1f}%")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze facility usage data and recommend best visit times"
    )
    parser.add_argument(
        "--facility",
        type=str,
        help="Name of the facility to analyze (e.g., 'CoRec')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show recommendations for all facilities"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    
    args = parser.parse_args()
    
    analyzer = FacilityAnalyzer()
    
    if args.all:
        facilities = analyzer.db.get_all_facilities()
        if not facilities:
            print("No facilities found in database.")
            print("Run collect_data.py first to gather data.")
            return
        
        for facility in facilities:
            analyzer.print_recommendations(facility, args.days)
    
    elif args.facility:
        analyzer.print_recommendations(args.facility, args.days)
    
    else:
        # Show all facilities and ask user to choose
        facilities = analyzer.db.get_all_facilities()
        if not facilities:
            print("No facilities found in database.")
            print("Run collect_data.py first to gather data.")
            return
        
        print("Available facilities:")
        for i, facility in enumerate(facilities, 1):
            print(f"  {i}. {facility}")
        
        print(f"\nUse --facility <name> to analyze a specific facility,")
        print(f"or --all to analyze all facilities.")


if __name__ == "__main__":
    main()
