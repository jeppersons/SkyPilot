from flask import Flask, jsonify
import psutil
import mysql.connector
from mysql.connector import Error
import os
import threading
import time

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': '192.168.8.161',  # or your MariaDB host
    'database': 'MCP',  # replace with your database name
    'user': 'ned',  # replace with your database username
    'password': 'ned'  # replace with your database password
}
POST_INTERVAL = 60  # Interval in seconds
HARDCODED_MACHINE_NAME = 'dusty'  # Hardcoded machine name

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        return None

def write_to_database(major, machine, measures):
    """Function to write stats to the database, one record per measure."""
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql = """INSERT INTO STATS_Machine (timestamp, Major, Minor, Value, Machine, Notes)
                     VALUES (NOW(), %s, %s, %s, %s, %s)"""
            for key, value in measures.items():
                minor_value = key[:3]  # Limit to first 3 characters
                notes = key  # Full label
                cursor.execute(sql, (major, minor_value, value, machine, notes))
            conn.commit()
        except Error as e:
            print(f"Error: {e}")
        finally:
            conn.close()
    else:
        print("Failed to get database connection")

def get_stats():
    """Collect system statistics."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_stats = psutil.virtual_memory()
    total_memory = memory_stats.total
    available_memory = memory_stats.available
    used_memory = memory_stats.used
    memory_percent = memory_stats.percent
    disk_usage = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()
    boot_time = psutil.boot_time()

    return {
        "cpu_percent": cpu_percent,
        "total_memory": total_memory,
        "available_memory": available_memory,
        "used_memory": used_memory,
        "memory_percent": memory_percent,
        "disk_total": disk_usage.total,
        "disk_used": disk_usage.used,
        "disk_free": disk_usage.free,
        "disk_percent": disk_usage.percent,
        "net_bytes_sent": net_io.bytes_sent,
        "net_bytes_recv": net_io.bytes_recv,
        "system_uptime": time.time() - boot_time
    }

def post_stats_periodically():
    """Function to post stats to the database periodically."""
    while True:
        major = "STATS"
        machine = HARDCODED_MACHINE_NAME
        measures = get_stats()
        write_to_database(major, machine, measures)
        time.sleep(POST_INTERVAL)

@app.route('/', methods=['GET'])
def stats_endpoint():
    """Endpoint to manually get stats."""
    return jsonify(get_stats())

if __name__ == '__main__':
    threading.Thread(target=post_stats_periodically, daemon=True).start()
    app.run(host='0.0.0.0', port=5001)
