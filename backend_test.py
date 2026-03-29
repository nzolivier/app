import requests
import sys
import json
from datetime import datetime

class AurenAPITester:
    def __init__(self, base_url="https://auren-reflect.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": None,
                "error": None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                result["error"] = response.text

            self.test_results.append(result)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        if success:
            print(f"   Response: {response}")
        return success

    def test_daily_reflection(self):
        """Test daily reflection endpoint"""
        success, response = self.run_test(
            "Daily Reflection",
            "GET",
            "daily-reflection",
            200
        )
        if success:
            # Validate response structure
            if 'en' in response and 'fr' in response:
                print(f"   English reflection: {response['en'][:50]}...")
                print(f"   French reflection: {response['fr'][:50]}...")
                return True
            else:
                print(f"❌ Invalid response structure: {response}")
                return False
        return False

    def test_chat_english(self):
        """Test chat endpoint with English message"""
        test_message = "I feel anxious about my future"
        success, response = self.run_test(
            "Chat - English Message",
            "POST",
            "chat",
            200,
            data={"message": test_message}
        )
        if success:
            if 'response' in response and 'language' in response:
                print(f"   Detected language: {response['language']}")
                print(f"   AI response: {response['response'][:100]}...")
                return response['language'] == 'en'
            else:
                print(f"❌ Invalid response structure: {response}")
                return False
        return False

    def test_chat_french(self):
        """Test chat endpoint with French message"""
        test_message = "Je me sens triste aujourd'hui"
        success, response = self.run_test(
            "Chat - French Message",
            "POST",
            "chat",
            200,
            data={"message": test_message}
        )
        if success:
            if 'response' in response and 'language' in response:
                print(f"   Detected language: {response['language']}")
                print(f"   AI response: {response['response'][:100]}...")
                return response['language'] == 'fr'
            else:
                print(f"❌ Invalid response structure: {response}")
                return False
        return False

    def test_chat_empty_message(self):
        """Test chat endpoint with empty message"""
        success, response = self.run_test(
            "Chat - Empty Message",
            "POST",
            "chat",
            400,
            data={"message": ""}
        )
        return success

    def test_chat_no_message(self):
        """Test chat endpoint with no message field"""
        success, response = self.run_test(
            "Chat - No Message Field",
            "POST",
            "chat",
            422,
            data={}
        )
        return success

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/test_reports/backend_test_{timestamp}.json"
        
        results = {
            "timestamp": timestamp,
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": f"{(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%",
            "test_details": self.test_results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Test results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    print("🚀 Starting AUREN Backend API Tests")
    print("=" * 50)
    
    tester = AurenAPITester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_daily_reflection,
        tester.test_chat_english,
        tester.test_chat_french,
        tester.test_chat_empty_message,
        tester.test_chat_no_message
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary:")
    print(f"   Total tests: {tester.tests_run}")
    print(f"   Passed: {tester.tests_passed}")
    print(f"   Failed: {tester.tests_run - tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%" if tester.tests_run > 0 else "0%")
    
    # Save results
    tester.save_results()
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())