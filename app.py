"""
Flask web application for CoRec Tracker.
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import threading
import time
import os
import sys

# Do not import scraper here - it pulls in Selenium/Chrome and can crash on Railway.
# Scraper is imported only inside collect_data_background() when actually needed.

app = Flask(__name__)

# DB and analyzer - initialized lazily on first use so app always starts (e.g. /health works)
db = None
analyzer = None
_db_init_error = None


def _ensure_db():
    """Initialize db and analyzer once, on first use. Returns True if ready."""
    global db, analyzer, _db_init_error
    if db is not None and analyzer is not None:
        return True
    if _db_init_error is not None:
        return False
    try:
        from database import FacilityDatabase
        from analyze import FacilityAnalyzer
        db = FacilityDatabase()
        analyzer = FacilityAnalyzer()
        return True
    except Exception as e:
        _db_init_error = str(e)
        print(f"Database/analyzer init failed: {_db_init_error}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

# Global flag for background task
collector_running = False
collector_thread = None


def collect_data_background():
    """Background task to collect facility usage data. Scraper imported here to avoid loading Selenium at app startup."""
    global collector_running
    scraper = None

    while collector_running:
        try:
            # Lazy-import so Railway never loads Selenium/Chrome at startup
            if scraper is None:
                from scraper import FacilityUsageScraper
                scraper = FacilityUsageScraper(headless=True)

            if not _ensure_db():
                time.sleep(60)
                continue

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collecting facility usage data...", file=sys.stderr)
            facilities = scraper.scrape()

            if facilities:
                count = 0
                for facility in facilities:
                    try:
                        db.insert_usage_data(
                            facility_name=facility['name'],
                            timestamp=facility['timestamp'],
                            occupancy=facility.get('occupancy'),
                            capacity=facility.get('capacity'),
                            percentage=facility.get('percentage'),
                            metadata={'source': 'web_scraper'}
                        )
                        count += 1
                    except Exception as db_err:
                        print(f"Error inserting {facility.get('name', 'unknown')}: {db_err}", file=sys.stderr)
                print(f"Successfully collected and saved data for {count}/{len(facilities)} facilities", file=sys.stderr)
            else:
                print("No facility data found in scrape result", file=sys.stderr)

        except Exception as e:
            print(f"Error collecting data: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Scraper may be broken (e.g. no Chrome); drop it so we retry creating it next loop
            try:
                if scraper:
                    scraper.close()
            except Exception:
                pass
            scraper = None

        # Wait 15 minutes before next collection
        for _ in range(900):  # 15 minutes = 900 seconds
            if not collector_running:
                break
            time.sleep(1)

    try:
        if scraper:
            scraper.close()
    except Exception:
        pass


def start_background_collector():
    """Start the background data collection task. Safe to call; failures are logged, not raised."""
    global collector_running, collector_thread

    if collector_running:
        print("Collector already running", file=sys.stderr)
        return False
    try:
        collector_running = True
        collector_thread = threading.Thread(target=collect_data_background, daemon=True)
        collector_thread.start()
        print("Background data collector started successfully", file=sys.stderr)
        return True
    except Exception as e:
        collector_running = False
        print(f"Could not start background collector: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def stop_background_collector():
    """Stop the background data collection task."""
    global collector_running
    collector_running = False
    print("Background data collector stopped")


@app.route('/health')
def health():
    """Health check - no DB required. Used by Railway to verify the app is up."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/debug')
def debug():
    """Debug endpoint to check environment and collector state."""
    import platform
    db_path = None
    db_exists = False
    db_size = 0
    if db:
        db_path = db.db_path
        db_exists = os.path.exists(db_path)
        if db_exists:
            try:
                db_size = os.path.getsize(db_path)
            except:
                pass
    
    facilities_count = 0
    total_data_points = 0
    if db:
        try:
            facilities = db.get_all_facilities()
            facilities_count = len(facilities)
            for facility in facilities:
                data = db.get_facility_data(facility)
                total_data_points += len(data)
        except Exception as e:
            pass
    
    return jsonify({
        'collector_running': collector_running,
        'enable_collector_env': os.environ.get('ENABLE_COLLECTOR', 'not set'),
        'db_initialized': db is not None,
        'db_path': db_path,
        'db_exists': db_exists,
        'db_size_bytes': db_size,
        'analyzer_initialized': analyzer is not None,
        'db_error': _db_init_error,
        'facilities_count': facilities_count,
        'total_data_points': total_data_points,
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'chromium_exists': os.path.exists('/usr/bin/chromium') or os.path.exists('/usr/bin/chromium-browser'),
        'chromedriver_exists': os.path.exists('/usr/bin/chromedriver')
    })


@app.errorhandler(Exception)
def handle_error(e):
    """Return a response instead of crashing so Railway sees a reply."""
    import traceback
    traceback.print_exc(file=sys.stderr)
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.route('/')
def index():
    """Main page."""
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({'error': 'Template failed', 'message': str(e)}), 500


def _db_required():
    """Return error response if DB failed to init (lazy init on first use)."""
    if not _ensure_db():
        return jsonify({'error': 'Database unavailable', 'detail': _db_init_error}), 503
    return None


@app.route('/api/facilities')
def get_facilities():
    """Get list of all facilities."""
    err = _db_required()
    if err:
        return err
    facilities = db.get_all_facilities()
    return jsonify({'facilities': facilities})


@app.route('/api/facility/<facility_name>/current')
def get_current_data(facility_name):
    """Get current/latest data for a facility."""
    err = _db_required()
    if err:
        return err
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
    err = _db_required()
    if err:
        return err
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
    err = _db_required()
    if err:
        return err
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
    err = _db_required()
    if err:
        # Return status even if DB failed, but mark DB as unavailable
        return jsonify({
            'collector_running': collector_running,
            'facilities_tracked': 0,
            'total_data_points': 0,
            'latest_collection': None,
            'db_available': False,
            'enable_collector_env': os.environ.get('ENABLE_COLLECTOR', 'not set')
        })
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
        'latest_collection': latest_time,
        'db_available': True,
        'enable_collector_env': os.environ.get('ENABLE_COLLECTOR', 'not set')
    })


@app.route('/api/collector/start', methods=['POST'])
def start_collector():
    """Start the background collector."""
    try:
        if start_background_collector():
            return jsonify({'status': 'started', 'message': 'Data collector started'})
        return jsonify({'status': 'already_running', 'message': 'Collector already running'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/collector/stop', methods=['POST'])
def stop_collector():
    """Stop the background collector."""
    stop_background_collector()
    return jsonify({'status': 'stopped', 'message': 'Data collector stopped'})


@app.route('/api/collector/test', methods=['POST'])
def test_collector():
    """Test collector by running one collection immediately. Returns results."""
    if not _ensure_db():
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        from scraper import FacilityUsageScraper
        scraper = FacilityUsageScraper(headless=True)
        
        print("Running test collection...", file=sys.stderr)
        facilities = scraper.scrape()
        
        if facilities:
            saved_count = 0
            for facility in facilities:
                try:
                    db.insert_usage_data(
                        facility_name=facility['name'],
                        timestamp=facility['timestamp'],
                        occupancy=facility.get('occupancy'),
                        capacity=facility.get('capacity'),
                        percentage=facility.get('percentage'),
                        metadata={'source': 'test_collection'}
                    )
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving {facility.get('name')}: {e}", file=sys.stderr)
            
            scraper.close()
            return jsonify({
                'status': 'success',
                'facilities_found': len(facilities),
                'facilities_saved': saved_count,
                'facilities': facilities[:5]  # Return first 5 as sample
            })
        else:
            scraper.close()
            return jsonify({
                'status': 'no_data',
                'message': 'Scraper returned no facilities'
            })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Test collection error: {error_trace}", file=sys.stderr)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': error_trace
        }), 500


# Start collector: locally always; on Railway only if ENABLE_COLLECTOR=1 (Chrome/Chromium must be installed via nixpacks.toml).
if __name__ == '__main__':
    start_background_collector()
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # Production mode (Gunicorn) - check env var
    enable_collector = os.environ.get('ENABLE_COLLECTOR', '').strip().lower()
    print(f"ENABLE_COLLECTOR env var: '{enable_collector}'", file=sys.stderr)
    if enable_collector in ('1', 'true', 'yes'):
        print("Attempting to start collector in production mode...", file=sys.stderr)
        if start_background_collector():
            print("Collector started successfully in production", file=sys.stderr)
        else:
            print("Collector failed to start in production", file=sys.stderr)
    else:
        print(f"Collector not started: ENABLE_COLLECTOR='{enable_collector}' (not in ['1', 'true', 'yes'])", file=sys.stderr)
