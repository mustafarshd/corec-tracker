"""
Flask web application for CoRec Tracker.
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import threading
import time
import schedule
from scraper import FacilityUsageScraper
from database import FacilityDatabase
from analyze import FacilityAnalyzer

app = Flask(__name__)
db = FacilityDatabase()
analyzer = FacilityAnalyzer()

# Global flag for background task
collector_running = False
collector_thread = None


def collect_data_background():
    """Background task to collect facility usage data."""
    global collector_running
    scraper = FacilityUsageScraper(headless=True)
    
    while collector_running:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collecting facility usage data...")
            facilities = scraper.scrape()
            
            if facilities:
                for facility in facilities:
                    db.insert_usage_data(
                        facility_name=facility['name'],
                        timestamp=facility['timestamp'],
                        occupancy=facility.get('occupancy'),
                        capacity=facility.get('capacity'),
                        percentage=facility.get('percentage'),
                        metadata={'source': 'web_scraper'}
                    )
                print(f"Collected data for {len(facilities)} facilities")
            else:
                print("No facility data found")
        
        except Exception as e:
            print(f"Error collecting data: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait 15 minutes before next collection
        for _ in range(900):  # 15 minutes = 900 seconds
            if not collector_running:
                break
            time.sleep(1)
    
    scraper.close()


def start_background_collector():
    """Start the background data collection task."""
    global collector_running, collector_thread
    
    if not collector_running:
        collector_running = True
        collector_thread = threading.Thread(target=collect_data_background, daemon=True)
        collector_thread.start()
        print("Background data collector started")
        return True
    return False


def stop_background_collector():
    """Stop the background data collection task."""
    global collector_running
    collector_running = False
    print("Background data collector stopped")


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/facilities')
def get_facilities():
    """Get list of all facilities."""
    facilities = db.get_all_facilities()
    return jsonify({'facilities': facilities})


@app.route('/api/facility/<facility_name>/current')
def get_current_data(facility_name):
    """Get current/latest data for a facility."""
    data = db.get_facility_data(facility_name)
    if data:
        latest = data[-1]  # Most recent
        return jsonify({
            'facility': facility_name,
            'data': latest,
            'total_points': len(data)
        })
    return jsonify({'error': 'No data found'}), 404


@app.route('/api/facility/<facility_name>/recommendations')
def get_recommendations(facility_name):
    """Get recommendations for a facility."""
    days = request.args.get('days', default=7, type=int)
    
    best_times = analyzer.get_best_times(facility_name, days_back=days, top_n=5)
    worst_times = analyzer.get_worst_times(facility_name, days_back=days, top_n=5)
    daily_patterns = analyzer.get_daily_patterns(facility_name, days_back=days)
    hourly_patterns = analyzer.get_hourly_patterns(facility_name, days_back=days)
    
    all_data = db.get_facility_data(facility_name)
    
    return jsonify({
        'facility': facility_name,
        'total_data_points': len(all_data),
        'days_analyzed': days,
        'best_times': best_times,
        'worst_times': worst_times,
        'daily_patterns': daily_patterns,
        'hourly_patterns': hourly_patterns
    })


@app.route('/api/facility/<facility_name>/history')
def get_history(facility_name):
    """Get historical data for a facility."""
    days = request.args.get('days', default=7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    data = db.get_facility_data(facility_name, start_date=start_date)
    
    return jsonify({
        'facility': facility_name,
        'data_points': len(data),
        'data': data
    })


@app.route('/api/status')
def get_status():
    """Get collector status."""
    global collector_running
    facilities = db.get_all_facilities()
    
    # Get total data points
    total_points = 0
    for facility in facilities:
        data = db.get_facility_data(facility)
        total_points += len(data)
    
    # Get latest collection time
    latest_time = None
    if facilities:
        data = db.get_facility_data(facilities[0])
        if data:
            latest_time = data[-1]['timestamp']
    
    return jsonify({
        'collector_running': collector_running,
        'facilities_tracked': len(facilities),
        'total_data_points': total_points,
        'latest_collection': latest_time
    })


@app.route('/api/collector/start', methods=['POST'])
def start_collector():
    """Start the background collector."""
    if start_background_collector():
        return jsonify({'status': 'started', 'message': 'Data collector started'})
    return jsonify({'status': 'already_running', 'message': 'Collector already running'})


@app.route('/api/collector/stop', methods=['POST'])
def stop_collector():
    """Stop the background collector."""
    stop_background_collector()
    return jsonify({'status': 'stopped', 'message': 'Data collector stopped'})


# Initialize collector on import (for production)
# In production, this will start when the app loads
if __name__ == '__main__':
    # Start background collector
    start_background_collector()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # Production mode - start collector when module is imported
    start_background_collector()
