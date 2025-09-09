#!/usr/bin/env python3
"""
Script to fix the resume_evaluations table schema by adding missing columns.
This script handles the case where the database schema is out of sync with the model.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError

def get_database_url():
    """Get database URL from environment variables."""
    return os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/linkedin_jobs')

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in the table."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = '{column_name}';
            """))
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking column {column_name}: {e}")
        return False

def add_missing_columns(engine):
    """Add missing columns to resume_evaluations table."""
    table_name = 'resume_evaluations'
    
    # Define the columns that should exist
    columns_to_add = [
        ('experience_points_score', 'INTEGER', 'NOT NULL DEFAULT 0'),
        ('job_relevance_score', 'INTEGER', 'NOT NULL DEFAULT 0'),
        ('quality_checks_score', 'INTEGER', 'NOT NULL DEFAULT 0'),
        ('critical_issues', 'JSON', 'NULL'),
        ('market_positioning', 'JSON', 'NULL'),
        ('evaluation_prompt', 'TEXT', 'NULL'),
    ]
    
    # Columns to modify
    columns_to_modify = [
        ('overall_score', 'INTEGER'),
        ('ats_compliance_score', 'INTEGER'),
        ('content_quality_score', 'INTEGER'),
    ]
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Add missing columns
                for column_name, data_type, constraints in columns_to_add:
                    if not check_column_exists(engine, table_name, column_name):
                        print(f"Adding column: {column_name}")
                        conn.execute(text(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN {column_name} {data_type} {constraints};
                        """))
                    else:
                        print(f"Column {column_name} already exists, skipping...")
                
                # Modify existing columns
                for column_name, new_type in columns_to_modify:
                    print(f"Modifying column: {column_name} to {new_type}")
                    conn.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN {column_name} TYPE {new_type};
                    """))
                
                # Update strengths and improvements to be JSON
                print("Converting strengths and improvements to JSON...")
                conn.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN strengths TYPE JSON USING strengths::JSON;
                """))
                
                conn.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN improvements TYPE JSON USING improvements::JSON;
                """))
                
                # Commit the transaction
                trans.commit()
                print("✅ Successfully updated resume_evaluations table schema!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error updating schema: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    return True

def main():
    """Main function to fix the database schema."""
    print("🔧 Fixing resume_evaluations table schema...")
    
    # Get database URL
    database_url = get_database_url()
    print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Add missing columns
        if add_missing_columns(engine):
            print("🎉 Schema fix completed successfully!")
        else:
            print("❌ Schema fix failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
