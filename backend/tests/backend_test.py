"""
Comprehensive API tests for Listrix AI Marketplace Operations Intelligence System
Tests all endpoints including Marketing Intelligence Agent, Vision AI, Control Layer, etc.
"""
import os
import requests
import sys
import time
import base64
from datetime import datetime

class ListrixAPITester:
    def __init__(self, base_url=None):
        base_url = base_url or os.environ.get("LISTRIX_TEST_BASE_URL", "http://localhost:8000")
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_item_id = None
        self.test_listing_id = None
        self.test_suggestion_id = None

    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {test_name}")
        else:
            print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })

    def test_api_root(self):
        """Test GET /api/ endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            if passed:
                data = response.json()
                details += f", Response: {data}"
            self.log_result("GET /api/ - API Root", passed, details)
            return passed
        except Exception as e:
            self.log_result("GET /api/ - API Root", False, f"Error: {str(e)}")
            return False

    def test_create_item(self):
        """Test POST /api/items endpoint"""
        test_item = {
            "name": f"Test Sony Headphones {datetime.now().strftime('%H%M%S')}",
            "description": "Sony WH-1000XM4 wireless headphones, excellent condition with original box",
            "condition": "Like New",
            "cost": 250.00,
            "category": "Electronics"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/items",
                json=test_item,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                required_fields = ["id", "name", "description", "condition", "created_at"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    passed = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    self.test_item_id = data['id']
                    details += f", Item ID: {data['id']}"
            else:
                details += f", Response: {response.text[:200]}"
            
            self.log_result("POST /api/items - Create Item", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/items - Create Item", False, f"Error: {str(e)}")
            return False

    def test_get_items(self):
        """Test GET /api/items endpoint"""
        try:
            response = requests.get(f"{self.api_url}/items", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                if not isinstance(data, list):
                    passed = False
                    details += ", Response is not a list"
                else:
                    details += f", Items count: {len(data)}"
            
            self.log_result("GET /api/items - Get Items", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/items - Get Items", False, f"Error: {str(e)}")
            return False

    def test_get_item_detail(self):
        """Test GET /api/items/{id} endpoint"""
        if not self.test_item_id:
            self.log_result("GET /api/items/{id} - Get Item Detail", False, "No test item ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/items/{self.test_item_id}", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Item: {data.get('name', 'N/A')}"
            
            self.log_result("GET /api/items/{id} - Get Item Detail", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/items/{id} - Get Item Detail", False, f"Error: {str(e)}")
            return False

    def test_ai_generate(self):
        """Test POST /api/ai/generate endpoint"""
        test_request = {
            "name": "iPhone 12 Pro 128GB",
            "description": "Used for 2 years, minor scratches on back, battery health 85%. Includes original box and charger.",
            "condition": "Good",
            "cost": 450.0,
            "item_id": self.test_item_id
        }
        
        try:
            print("   ⏳ Generating AI listing (may take 5-15 seconds)...")
            response = requests.post(
                f"{self.api_url}/ai/generate",
                json=test_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                required_fields = ["id", "listing_title", "listing_description", "suggested_price", "hashtags"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    passed = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    self.test_listing_id = data['id']
                    details += f", Title: '{data['listing_title'][:50]}...', Price: ${data['suggested_price']}"
            else:
                details += f", Response: {response.text[:200]}"
            
            self.log_result("POST /api/ai/generate - Generate Listing", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/ai/generate - Generate Listing", False, f"Error: {str(e)}")
            return False

    def test_get_listings(self):
        """Test GET /api/listings endpoint"""
        try:
            response = requests.get(f"{self.api_url}/listings", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Listings count: {len(data)}"
            
            self.log_result("GET /api/listings - Get Listings", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/listings - Get Listings", False, f"Error: {str(e)}")
            return False

    def test_get_events(self):
        """Test GET /api/events endpoint"""
        try:
            response = requests.get(f"{self.api_url}/events", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Events count: {len(data)}"
            
            self.log_result("GET /api/events - Get Events", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/events - Get Events", False, f"Error: {str(e)}")
            return False

    def test_analyze_item(self):
        """Test POST /api/ai/analyze/{item_id} - Marketing Intelligence Agent"""
        if not self.test_item_id:
            self.log_result("POST /api/ai/analyze/{id} - Analyze Item", False, "No test item ID available")
            return False
        
        try:
            print("   ⏳ Running Marketing Intelligence analysis (may take 10-20 seconds)...")
            response = requests.post(f"{self.api_url}/ai/analyze/{self.test_item_id}", timeout=40)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                if 'performance' in data and 'suggestions' in data:
                    perf = data['performance']
                    suggs = data['suggestions']
                    details += f", Performance: {perf.get('status', 'N/A')}, Suggestions: {len(suggs)}"
                    if len(suggs) > 0:
                        self.test_suggestion_id = suggs[0]['id']
                else:
                    passed = False
                    details += ", Missing performance or suggestions"
            else:
                details += f", Response: {response.text[:200]}"
            
            self.log_result("POST /api/ai/analyze/{id} - Analyze Item", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/ai/analyze/{id} - Analyze Item", False, f"Error: {str(e)}")
            return False

    def test_analyze_all(self):
        """Test POST /api/ai/analyze-all - Run Marketing Analysis on all items"""
        try:
            print("   ⏳ Running Marketing Analysis on all items (may take 15-30 seconds)...")
            response = requests.post(f"{self.api_url}/ai/analyze-all", timeout=60)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Analyzed: {data.get('analyzed', 0)} items"
            
            self.log_result("POST /api/ai/analyze-all - Analyze All Items", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/ai/analyze-all - Analyze All Items", False, f"Error: {str(e)}")
            return False

    def test_get_performance(self):
        """Test GET /api/performance endpoint"""
        try:
            response = requests.get(f"{self.api_url}/performance", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Performance records: {len(data)}"
            
            self.log_result("GET /api/performance - Get Performance", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/performance - Get Performance", False, f"Error: {str(e)}")
            return False

    def test_get_suggestions(self):
        """Test GET /api/suggestions endpoint"""
        try:
            response = requests.get(f"{self.api_url}/suggestions?status=pending", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Pending suggestions: {len(data)}"
            
            self.log_result("GET /api/suggestions - Get Suggestions", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/suggestions - Get Suggestions", False, f"Error: {str(e)}")
            return False

    def test_dismiss_suggestion(self):
        """Test POST /api/suggestions/{id}/dismiss - Control Layer reject"""
        if not self.test_suggestion_id:
            self.log_result("POST /api/suggestions/{id}/dismiss - Dismiss Suggestion", False, "No test suggestion ID available")
            return False
        
        try:
            response = requests.post(f"{self.api_url}/suggestions/{self.test_suggestion_id}/dismiss", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Status: {data.get('status', 'N/A')}"
            
            self.log_result("POST /api/suggestions/{id}/dismiss - Dismiss Suggestion", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/suggestions/{id}/dismiss - Dismiss Suggestion", False, f"Error: {str(e)}")
            return False

    def test_performance_intelligence(self):
        """Test GET /api/performance-intelligence endpoint"""
        try:
            response = requests.get(f"{self.api_url}/performance-intelligence", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Best: {len(data.get('best_performing', []))}, Worst: {len(data.get('worst_performing', []))}"
            
            self.log_result("GET /api/performance-intelligence - Performance Intelligence", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/performance-intelligence - Performance Intelligence", False, f"Error: {str(e)}")
            return False

    def test_market_signals(self):
        """Test GET /api/market/signals endpoint"""
        try:
            response = requests.get(f"{self.api_url}/market/signals", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Market signals: {len(data)}"
            
            self.log_result("GET /api/market/signals - Market Signals", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/market/signals - Market Signals", False, f"Error: {str(e)}")
            return False

    def test_generate_brief(self):
        """Test POST /api/brief/generate - Daily AI Briefing"""
        try:
            print("   ⏳ Generating Daily AI Briefing (may take 10-20 seconds)...")
            response = requests.post(f"{self.api_url}/brief/generate", timeout=40)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Headline: '{data.get('headline', 'N/A')[:50]}...'"
            
            self.log_result("POST /api/brief/generate - Generate Brief", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/brief/generate - Generate Brief", False, f"Error: {str(e)}")
            return False

    def test_get_brief_latest(self):
        """Test GET /api/brief/latest endpoint"""
        try:
            response = requests.get(f"{self.api_url}/brief/latest", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                if data:
                    details += f", Headline: '{data.get('headline', 'N/A')[:40]}...'"
                else:
                    details += ", No brief available yet"
            
            self.log_result("GET /api/brief/latest - Get Latest Brief", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/brief/latest - Get Latest Brief", False, f"Error: {str(e)}")
            return False

    def test_ai_assistant(self):
        """Test POST /api/ai/assistant - Live AI Assistant"""
        try:
            print("   ⏳ Asking AI Assistant (may take 5-15 seconds)...")
            response = requests.post(
                f"{self.api_url}/ai/assistant",
                json={"query": "How is my business doing?", "voice": False},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                if 'answer' in data:
                    details += f", Answer: '{data['answer'][:50]}...'"
                else:
                    passed = False
                    details += ", Missing answer field"
            
            self.log_result("POST /api/ai/assistant - AI Assistant", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/ai/assistant - AI Assistant", False, f"Error: {str(e)}")
            return False

    def test_integrations(self):
        """Test GET /api/integrations endpoint"""
        try:
            response = requests.get(f"{self.api_url}/integrations", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Connectors: {len(data)}"
            
            self.log_result("GET /api/integrations - List Integrations", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/integrations - List Integrations", False, f"Error: {str(e)}")
            return False

    def test_integration_connect(self):
        """Test POST /api/integrations/{platform}/connect endpoint"""
        try:
            response = requests.post(f"{self.api_url}/integrations/TradeMe/connect", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Auth status: {data.get('auth_status', 'N/A')}"
            
            self.log_result("POST /api/integrations/{platform}/connect - Connect Integration", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/integrations/{platform}/connect - Connect Integration", False, f"Error: {str(e)}")
            return False

    def test_integration_sync(self):
        """Test POST /api/integrations/{platform}/sync endpoint"""
        try:
            response = requests.post(f"{self.api_url}/integrations/TradeMe/sync", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Simulated: {data.get('simulated', False)}"
            
            self.log_result("POST /api/integrations/{platform}/sync - Sync Integration", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/integrations/{platform}/sync - Sync Integration", False, f"Error: {str(e)}")
            return False

    def test_inbox_refresh(self):
        """Test POST /api/inbox/refresh endpoint"""
        try:
            response = requests.post(f"{self.api_url}/inbox/refresh", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Messages created: {data.get('count', 0)}"
            
            self.log_result("POST /api/inbox/refresh - Refresh Inbox", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("POST /api/inbox/refresh - Refresh Inbox", False, f"Error: {str(e)}")
            return False

    def test_get_inbox(self):
        """Test GET /api/inbox endpoint"""
        try:
            response = requests.get(f"{self.api_url}/inbox", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Messages: {len(data)}"
            
            self.log_result("GET /api/inbox - Get Inbox", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/inbox - Get Inbox", False, f"Error: {str(e)}")
            return False

    def test_price_history(self):
        """Test GET /api/price-history/{item_id} endpoint"""
        if not self.test_item_id:
            self.log_result("GET /api/price-history/{id} - Price History", False, "No test item ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/price-history/{self.test_item_id}", timeout=10)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if passed:
                data = response.json()
                details += f", Price changes: {len(data)}"
            
            self.log_result("GET /api/price-history/{id} - Price History", passed, details)
            return passed
            
        except Exception as e:
            self.log_result("GET /api/price-history/{id} - Price History", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("=" * 70)
        print("LISTRIX AI MARKETPLACE OPERATIONS INTELLIGENCE - BACKEND API TESTS")
        print(f"Testing: {self.base_url}")
        print("=" * 70)
        print()
        
        # Core CRUD
        print("📦 CORE CRUD OPERATIONS")
        self.test_api_root()
        self.test_create_item()
        self.test_get_items()
        self.test_get_item_detail()
        self.test_ai_generate()
        self.test_get_listings()
        self.test_get_events()
        print()
        
        # Marketing Intelligence Agent
        print("🤖 MARKETING INTELLIGENCE AGENT")
        self.test_analyze_item()
        self.test_analyze_all()
        self.test_get_performance()
        self.test_get_suggestions()
        self.test_dismiss_suggestion()
        self.test_performance_intelligence()
        self.test_market_signals()
        self.test_price_history()
        print()
        
        # AI Features
        print("✨ AI FEATURES")
        self.test_generate_brief()
        self.test_get_brief_latest()
        self.test_ai_assistant()
        print()
        
        # Integration Hub
        print("🔌 INTEGRATION HUB")
        self.test_integrations()
        self.test_integration_connect()
        self.test_integration_sync()
        print()
        
        # Smart Inbox
        print("📬 SMART INBOX")
        self.test_inbox_refresh()
        self.test_get_inbox()
        print()
        
        # Summary
        print("=" * 70)
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} PASSED")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print("=" * 70)
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED")
            return 0
        else:
            failed = self.tests_run - self.tests_passed
            print(f"❌ {failed} TEST(S) FAILED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}")
            return 1

def main():
    tester = ListrixAPITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
