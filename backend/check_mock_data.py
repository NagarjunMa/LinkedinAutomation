
import sys
import os
from sqlalchemy import create_engine, text

# Add the backend directory to the path so we can import app modules if needed
# (though for a direct DB script, we just need the connection string)
backend_dir = '/Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend'
sys.path.append(backend_dir)

from app.core.config import settings

def clean_mock_data():
    database_url = settings.DATABASE_URL
    if not database_url:
        print("DATABASE_URL not set in settings")
        return

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            # 1. Check for suspicious data (e.g. "Mock", "Test", "Example" in title or company)
            # Adjust the WHERE clause as needed based on what "mock data" looks like
            check_query = text("""
                SELECT id, title, company, description 
                FROM jobs 
                WHERE 
                    title ILIKE '%mock%' OR 
                    title ILIKE '%test%' OR 
                    company ILIKE '%mock%' OR 
                    company ILIKE '%test%' OR
                    company = 'Unknown Company' OR
                    description ILIKE '%mock%'
            """)
            
            result = connection.execute(check_query)
            rows = result.fetchall()
            
            if not rows:
                print("No obvious mock data found in 'jobs' table based on title/company keywords.")
            else:
                print(f"Found {len(rows)} potential mock entries:")
                for row in rows:
                    print(f" - ID: {row[0]}, Title: {row[1]}, Company: {row[2]}")
                
                # Uncomment to actually delete
                # delete_query = text("""
                #     DELETE FROM jobs 
                #     WHERE 
                #         title ILIKE '%mock%' OR 
                #         title ILIKE '%test%' OR 
                #         company ILIKE '%mock%' OR 
                #         company ILIKE '%test%' OR
                #         company = 'Unknown Company' OR
                #         description ILIKE '%mock%'
                # """)
                # connection.execute(delete_query)
                # connection.commit()
                # print("Deleted mock entries.")

            # Also check TOTAL count to see if there's a huge number of rows
            count_result = connection.execute(text("SELECT COUNT(*) FROM jobs"))
            total_count = count_result.scalar()
            print(f"Total jobs in database: {total_count}")

    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    clean_mock_data()
