# test_units.py
import unittest
from unittest.mock import MagicMock, patch
import sqlite3
import re

# Import components from your project files
import database
import remote_jobs_rss

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        """Set up an isolated, temporary in-memory database for every test."""
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Override database.getConnection to return our mock in-memory connection
        self.original_get_connection = database.getConnection
        database.getConnection = lambda: self.conn
        
        # Initialize schema cleanly by letting SQLite parse the full file natively
        with open(database.SCHEMA_PATH, 'r', encoding='utf-8') as f:
            raw_sql = f.read()
            
        # Normalize Windows line endings (\r\n) to \n so executescript doesn't trip on comments
        normalized_sql = raw_sql.replace('\r\n', '\n')
        
        # Run the entire script natively
        self.conn.executescript(normalized_sql)

    def tearDown(self):
        """Clean up and restore original connection function."""
        self.conn.close()
        database.getConnection = self.original_get_connection

    def test_insert_and_search_job(self):
        """Test inserting a job and retrieving it via search."""
        sample_job = {
            "title": "Python Engineer",
            "company": "Tech Corp",
            "loc": "Remote",
            "is_remote": 1,
            "location_scope": "remote_worldwide",
            "job_type": "FT",
            "category": "software",
            "job_description": "We need a Python dev.",
            "link": "https://example.com/job1",
            "job_board": "weworkremotely",
            "date_posted": "2026-06-20"
        }
        
        # Test Insertion
        inserted = database.insert_job(sample_job)
        self.assertTrue(inserted)
        
        # Test Duplicate Prevention (link is UNIQUE)
        duplicate_inserted = database.insert_job(sample_job)
        self.assertFalse(duplicate_inserted)
        
        # Test Search Filter
        results = database.search_jobs(keywords=["Python"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["company"], "Tech Corp")

    def test_save_and_update_job_status(self):
        """Test saving a job and updating its application pipeline status."""
        # Insert a baseline job first
        self.conn.execute(
            "INSERT INTO jobs (title, link) VALUES (?, ?)", 
            ("Frontend Dev", "https://example.com/job2")
        )
        job_id = self.conn.execute("SELECT id FROM jobs").fetchone()[0]
        
        # Save the job
        saved = database.save_job(job_id=job_id, status="saved")
        self.assertTrue(saved)
        
        # Update status
        updated = database.update_saved_job_status(job_id=job_id, status="interviewing")
        self.assertTrue(updated)
        
        # Fetch and verify
        saved_jobs = database.get_saved_jobs()
        self.assertEqual(len(saved_jobs), 1)
        self.assertEqual(saved_jobs[0]["job_status"], "interviewing")


class TestDataInferenceAndParsing(unittest.TestCase):
    def test_get_job_type(self):
        """Verify job type string inference handles patterns appropriately."""
        # Test freelance matching
        self.assertEqual(remote_jobs_rss.get_job_type("Looking for a Freelancer", "Blah"), "FREE")
        # Test contract matching
        self.assertEqual(remote_jobs_rss.get_job_type("Dev Role", "This is a 1099 independent contractor role"), "CON")
        # Test default fallback
        self.assertEqual(remote_jobs_rss.get_job_type("Engineer", "Standard job description"), "FT")

    def test_get_location_scope(self):
        """Verify geographic targeting maps correctly."""
        self.assertEqual(
            remote_jobs_rss.get_location_scope("React Developer (US Only)", "Must be located in the USA"), 
            "remote_us_only"
        )
        self.assertEqual(
            remote_jobs_rss.get_location_scope("Go Developer", "Work from anywhere in the world!"), 
            "remote_worldwide"
        )

    @patch('remote_jobs_rss.GoogleTranslator')
    def test_clean_wwr_entry(self, mock_translator):
        """Mock the external translation API to test parsing logic purely."""
        # Set up a mock translation payload return string
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Mocked Translated Text"
        mock_translator.return_value = mock_instance

        # Fake feedparser dict element
        fake_entry = {
            "title": "Basecamp : Desarrollador de Software Senior",
            "summary": "<p>Headquarters: Chicago URL: https://basecamp.com</p><p>Job details here...</p>",
            "tags": [{"term": "Software Development"}],
            "link": "https://weworkremotely.com/jobs/123",
            "published_parsed": (2026, 6, 20, 0, 0, 0, 5, 171, 0)
        }

        cleaned = remote_jobs_rss.clean_wwr_entry(fake_entry, "weworkremotely")
        
        self.assertIsNotNone(cleaned)
        self.assertEqual(cleaned["company"], "Basecamp")
        self.assertEqual(cleaned["title"], "Mocked Translated Text")
        self.assertEqual(cleaned["category"], "software_development")


if __name__ == '__main__':
    unittest.main()