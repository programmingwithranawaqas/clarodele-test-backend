#!/usr/bin/env python3
"""
Quick test script to verify Google Drive URL parsing and basic functionality
"""

import re
from typing import Optional


def extract_google_drive_id(url: str) -> Optional[str]:
    """Extract file ID from Google Drive URL"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/open\?id=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def test_url_parsing():
    """Test various Google Drive URL formats"""
    test_urls = [
        "https://drive.google.com/file/d/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE/view?usp=drivesdk",
        "https://drive.google.com/file/d/1ABC123xyz/view",
        "https://drive.google.com/open?id=1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE",
        "https://drive.google.com/uc?id=1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE&export=download",
    ]
    
    print("Testing Google Drive URL Parsing")
    print("=" * 70)
    
    for url in test_urls:
        file_id = extract_google_drive_id(url)
        status = "✓" if file_id else "✗"
        print(f"{status} URL: {url[:60]}...")
        print(f"  File ID: {file_id if file_id else 'NOT FOUND'}")
        print()
    
    # Test the specific URL from the user
    print("\nTesting User's Specific URL:")
    print("=" * 70)
    user_url = "https://drive.google.com/file/d/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE/view?usp=drivesdk"
    file_id = extract_google_drive_id(user_url)
    print(f"URL: {user_url}")
    print(f"Extracted ID: {file_id}")
    print(f"GCS Path: listening_tarea1/{file_id}.mp3")
    print(f"Full GCS URL: gs://clarodele-mvp-content/listening_tarea1/{file_id}.mp3")


if __name__ == "__main__":
    test_url_parsing()
