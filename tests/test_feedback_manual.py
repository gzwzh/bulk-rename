import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.feedback_api import FeedbackAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_get_feedback_url():
    print("Testing FeedbackAPI.get_feedback_url()...")
    url = FeedbackAPI.get_feedback_url()
    if url:
        print(f"SUCCESS: Retrieved URL: {url}")
    else:
        print("FAILURE: Could not retrieve URL")

if __name__ == "__main__":
    test_get_feedback_url()
