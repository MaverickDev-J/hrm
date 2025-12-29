import psycopg2

try:
    conn = psycopg2.connect(
        dbname="hr_management_db",
        user="hruser",
        password="hrpass123",
        host="localhost",
        port="5433"
    )
    print("✅ Postgres connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ PostgreSQL version: {version[: 50]}...")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")