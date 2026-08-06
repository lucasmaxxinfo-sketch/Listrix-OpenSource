"""
CRITICAL: Multi-Workspace Data Isolation Tests for Listrix
Tests COMPLETE data isolation between workspaces - the P0 priority requirement.
Every DB query and insert MUST be scoped by workspace_id via X-Workspace-Id header.
"""
import os
import requests
import sys
import time
from datetime import datetime

class WorkspaceIsolationTester:
    def __init__(self, base_url=None):
        base_url = base_url or os.environ.get("LISTRIX_TEST_BASE_URL", "http://localhost:8000")
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Workspace data
        self.workspace_a_id = None
        self.workspace_b_id = None
        self.default_workspace_id = None
        
        # Workspace A resources
        self.item_a_id = None
        self.listing_a_id = None
        self.suggestion_a_id = None
        
        # Workspace B resources
        self.item_b_id = None
        self.listing_b_id = None
        self.suggestion_b_id = None

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

    def test_create_workspaces(self):
        """Create 2 test workspaces"""
        try:
            # Create Workspace A
            workspace_a = {
                "name": f"Test Business A {datetime.now().strftime('%H%M%S')}",
                "primary_color": "#FF0000",
                "currency": "USD",
                "business_type": "Reseller"
            }
            response_a = requests.post(f"{self.api_url}/workspaces", json=workspace_a, timeout=10)
            
            if response_a.status_code != 200:
                self.log_result("Create Workspace A", False, f"Status: {response_a.status_code}, Response: {response_a.text[:200]}")
                return False
            
            data_a = response_a.json()
            self.workspace_a_id = data_a['id']
            
            # Create Workspace B
            workspace_b = {
                "name": f"Test Business B {datetime.now().strftime('%H%M%S')}",
                "primary_color": "#0000FF",
                "currency": "EUR",
                "business_type": "Reseller"
            }
            response_b = requests.post(f"{self.api_url}/workspaces", json=workspace_b, timeout=10)
            
            if response_b.status_code != 200:
                self.log_result("Create Workspace B", False, f"Status: {response_b.status_code}, Response: {response_b.text[:200]}")
                return False
            
            data_b = response_b.json()
            self.workspace_b_id = data_b['id']
            
            # Get default workspace
            response_default = requests.get(f"{self.api_url}/workspaces", timeout=10)
            if response_default.status_code == 200:
                workspaces = response_default.json()
                for ws in workspaces:
                    if ws.get('is_default'):
                        self.default_workspace_id = ws['id']
                        break
            
            self.log_result("Create Test Workspaces", True, f"Workspace A: {self.workspace_a_id}, Workspace B: {self.workspace_b_id}, Default: {self.default_workspace_id}")
            return True
            
        except Exception as e:
            self.log_result("Create Test Workspaces", False, f"Error: {str(e)}")
            return False

    def test_create_items_in_workspaces(self):
        """Create items in both workspaces"""
        try:
            # Create item in Workspace A
            item_a = {
                "name": "Workspace A Item - Sony Headphones",
                "description": "This item belongs to Workspace A only",
                "condition": "Like New",
                "cost": 250.00,
                "category": "Electronics"
            }
            response_a = requests.post(
                f"{self.api_url}/items",
                json=item_a,
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Create Item in Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            data_a = response_a.json()
            self.item_a_id = data_a['id']
            
            # Create item in Workspace B
            item_b = {
                "name": "Workspace B Item - iPhone 12",
                "description": "This item belongs to Workspace B only",
                "condition": "Good",
                "cost": 450.00,
                "category": "Electronics"
            }
            response_b = requests.post(
                f"{self.api_url}/items",
                json=item_b,
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Create Item in Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            data_b = response_b.json()
            self.item_b_id = data_b['id']
            
            self.log_result("Create Items in Both Workspaces", True, f"Item A: {self.item_a_id}, Item B: {self.item_b_id}")
            return True
            
        except Exception as e:
            self.log_result("Create Items in Both Workspaces", False, f"Error: {str(e)}")
            return False

    def test_items_isolation_read(self):
        """CRITICAL: Verify GET /api/items returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header - should only see Workspace A items
            response_a = requests.get(
                f"{self.api_url}/items",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Items Isolation - Workspace A Query", False, f"Status: {response_a.status_code}")
                return False
            
            items_a = response_a.json()
            item_a_names = [item['name'] for item in items_a]
            
            # Check that Workspace B item is NOT in Workspace A results
            workspace_b_leaked = any("Workspace B Item" in name for name in item_a_names)
            
            if workspace_b_leaked:
                self.log_result("Items Isolation - Workspace A Query", False, f"DATA LEAK: Workspace B item found in Workspace A query! Items: {item_a_names}")
                return False
            
            # Query with Workspace B header - should only see Workspace B items
            response_b = requests.get(
                f"{self.api_url}/items",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Items Isolation - Workspace B Query", False, f"Status: {response_b.status_code}")
                return False
            
            items_b = response_b.json()
            item_b_names = [item['name'] for item in items_b]
            
            # Check that Workspace A item is NOT in Workspace B results
            workspace_a_leaked = any("Workspace A Item" in name for name in item_b_names)
            
            if workspace_a_leaked:
                self.log_result("Items Isolation - Workspace B Query", False, f"DATA LEAK: Workspace A item found in Workspace B query! Items: {item_b_names}")
                return False
            
            self.log_result("Items Isolation - Read", True, f"Workspace A sees {len(items_a)} items, Workspace B sees {len(items_b)} items. No cross-workspace leakage.")
            return True
            
        except Exception as e:
            self.log_result("Items Isolation - Read", False, f"Error: {str(e)}")
            return False

    def test_item_detail_cross_workspace_protection(self):
        """CRITICAL: Verify GET /api/items/{id} with wrong workspace header returns 404"""
        try:
            # Try to access Workspace A item with Workspace B header - should return 404
            response = requests.get(
                f"{self.api_url}/items/{self.item_a_id}",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_result("Item Detail Cross-Workspace Protection", False, f"SECURITY BREACH: Workspace B can read Workspace A item! Status: {response.status_code}")
                return False
            
            if response.status_code != 404:
                self.log_result("Item Detail Cross-Workspace Protection", False, f"Expected 404, got {response.status_code}")
                return False
            
            self.log_result("Item Detail Cross-Workspace Protection", True, "Workspace B cannot access Workspace A item (404)")
            return True
            
        except Exception as e:
            self.log_result("Item Detail Cross-Workspace Protection", False, f"Error: {str(e)}")
            return False

    def test_generate_listings_in_workspaces(self):
        """Generate listings in both workspaces"""
        try:
            # Generate listing in Workspace A
            print("   ⏳ Generating listing for Workspace A (5-15s)...")
            listing_a = {
                "name": "Workspace A Item - Sony Headphones",
                "description": "This listing belongs to Workspace A only",
                "condition": "Like New",
                "cost": 250.00,
                "item_id": self.item_a_id
            }
            response_a = requests.post(
                f"{self.api_url}/ai/generate",
                json=listing_a,
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=30
            )
            
            if response_a.status_code != 200:
                self.log_result("Generate Listing in Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            data_a = response_a.json()
            self.listing_a_id = data_a['id']
            
            # Generate listing in Workspace B
            print("   ⏳ Generating listing for Workspace B (5-15s)...")
            listing_b = {
                "name": "Workspace B Item - iPhone 12",
                "description": "This listing belongs to Workspace B only",
                "condition": "Good",
                "cost": 450.00,
                "item_id": self.item_b_id
            }
            response_b = requests.post(
                f"{self.api_url}/ai/generate",
                json=listing_b,
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=30
            )
            
            if response_b.status_code != 200:
                self.log_result("Generate Listing in Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            data_b = response_b.json()
            self.listing_b_id = data_b['id']
            
            self.log_result("Generate Listings in Both Workspaces", True, f"Listing A: {self.listing_a_id}, Listing B: {self.listing_b_id}")
            return True
            
        except Exception as e:
            self.log_result("Generate Listings in Both Workspaces", False, f"Error: {str(e)}")
            return False

    def test_listings_isolation_read(self):
        """CRITICAL: Verify GET /api/listings returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/listings",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Listings Isolation - Workspace A Query", False, f"Status: {response_a.status_code}")
                return False
            
            listings_a = response_a.json()
            listing_a_sources = [listing.get('source_name', '') for listing in listings_a]
            
            # Check for leakage
            workspace_b_leaked = any("Workspace B Item" in name for name in listing_a_sources)
            
            if workspace_b_leaked:
                self.log_result("Listings Isolation - Workspace A Query", False, f"DATA LEAK: Workspace B listing found in Workspace A query!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/listings",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Listings Isolation - Workspace B Query", False, f"Status: {response_b.status_code}")
                return False
            
            listings_b = response_b.json()
            listing_b_sources = [listing.get('source_name', '') for listing in listings_b]
            
            # Check for leakage
            workspace_a_leaked = any("Workspace A Item" in name for name in listing_b_sources)
            
            if workspace_a_leaked:
                self.log_result("Listings Isolation - Workspace B Query", False, f"DATA LEAK: Workspace A listing found in Workspace B query!")
                return False
            
            self.log_result("Listings Isolation - Read", True, f"Workspace A sees {len(listings_a)} listings, Workspace B sees {len(listings_b)} listings. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Listings Isolation - Read", False, f"Error: {str(e)}")
            return False

    def test_events_isolation_read(self):
        """CRITICAL: Verify GET /api/events returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/events",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Events Isolation - Workspace A Query", False, f"Status: {response_a.status_code}")
                return False
            
            events_a = response_a.json()
            event_a_messages = [event.get('message', '') for event in events_a]
            
            # Check for leakage
            workspace_b_leaked = any("Workspace B Item" in msg for msg in event_a_messages)
            
            if workspace_b_leaked:
                self.log_result("Events Isolation - Workspace A Query", False, f"DATA LEAK: Workspace B event found in Workspace A query!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/events",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Events Isolation - Workspace B Query", False, f"Status: {response_b.status_code}")
                return False
            
            events_b = response_b.json()
            event_b_messages = [event.get('message', '') for event in events_b]
            
            # Check for leakage
            workspace_a_leaked = any("Workspace A Item" in msg for msg in event_b_messages)
            
            if workspace_a_leaked:
                self.log_result("Events Isolation - Workspace B Query", False, f"DATA LEAK: Workspace A event found in Workspace B query!")
                return False
            
            self.log_result("Events Isolation - Read", True, f"Workspace A sees {len(events_a)} events, Workspace B sees {len(events_b)} events. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Events Isolation - Read", False, f"Error: {str(e)}")
            return False

    def test_analyze_items_in_workspaces(self):
        """Run analysis in both workspaces to generate suggestions"""
        try:
            # Analyze item in Workspace A
            print("   ⏳ Analyzing item in Workspace A (10-20s)...")
            response_a = requests.post(
                f"{self.api_url}/ai/analyze/{self.item_a_id}",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=40
            )
            
            if response_a.status_code != 200:
                self.log_result("Analyze Item in Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            data_a = response_a.json()
            if 'suggestions' in data_a and len(data_a['suggestions']) > 0:
                self.suggestion_a_id = data_a['suggestions'][0]['id']
            
            # Analyze item in Workspace B
            print("   ⏳ Analyzing item in Workspace B (10-20s)...")
            response_b = requests.post(
                f"{self.api_url}/ai/analyze/{self.item_b_id}",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=40
            )
            
            if response_b.status_code != 200:
                self.log_result("Analyze Item in Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            data_b = response_b.json()
            if 'suggestions' in data_b and len(data_b['suggestions']) > 0:
                self.suggestion_b_id = data_b['suggestions'][0]['id']
            
            self.log_result("Analyze Items in Both Workspaces", True, f"Suggestion A: {self.suggestion_a_id}, Suggestion B: {self.suggestion_b_id}")
            return True
            
        except Exception as e:
            self.log_result("Analyze Items in Both Workspaces", False, f"Error: {str(e)}")
            return False

    def test_analyze_cross_workspace_protection(self):
        """CRITICAL: Verify POST /api/ai/analyze/{item_id} with wrong workspace header returns 404"""
        try:
            # Try to analyze Workspace A item with Workspace B header - should return 404
            response = requests.post(
                f"{self.api_url}/ai/analyze/{self.item_a_id}",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=40
            )
            
            if response.status_code == 200:
                self.log_result("Analyze Cross-Workspace Protection", False, f"SECURITY BREACH: Workspace B can analyze Workspace A item! Status: {response.status_code}")
                return False
            
            if response.status_code != 404:
                self.log_result("Analyze Cross-Workspace Protection", False, f"Expected 404, got {response.status_code}")
                return False
            
            self.log_result("Analyze Cross-Workspace Protection", True, "Workspace B cannot analyze Workspace A item (404)")
            return True
            
        except Exception as e:
            self.log_result("Analyze Cross-Workspace Protection", False, f"Error: {str(e)}")
            return False

    def test_suggestions_isolation_read(self):
        """CRITICAL: Verify GET /api/suggestions returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/suggestions",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Suggestions Isolation - Workspace A Query", False, f"Status: {response_a.status_code}")
                return False
            
            suggestions_a = response_a.json()
            suggestion_a_items = [sugg.get('item_name', '') for sugg in suggestions_a]
            
            # Check for leakage
            workspace_b_leaked = any("Workspace B Item" in name for name in suggestion_a_items)
            
            if workspace_b_leaked:
                self.log_result("Suggestions Isolation - Workspace A Query", False, f"DATA LEAK: Workspace B suggestion found in Workspace A query!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/suggestions",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Suggestions Isolation - Workspace B Query", False, f"Status: {response_b.status_code}")
                return False
            
            suggestions_b = response_b.json()
            suggestion_b_items = [sugg.get('item_name', '') for sugg in suggestions_b]
            
            # Check for leakage
            workspace_a_leaked = any("Workspace A Item" in name for name in suggestion_b_items)
            
            if workspace_a_leaked:
                self.log_result("Suggestions Isolation - Workspace B Query", False, f"DATA LEAK: Workspace A suggestion found in Workspace B query!")
                return False
            
            self.log_result("Suggestions Isolation - Read", True, f"Workspace A sees {len(suggestions_a)} suggestions, Workspace B sees {len(suggestions_b)} suggestions. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Suggestions Isolation - Read", False, f"Error: {str(e)}")
            return False

    def test_suggestion_apply_cross_workspace_protection(self):
        """CRITICAL: Verify POST /api/suggestions/{id}/apply with wrong workspace header returns 404"""
        if not self.suggestion_a_id:
            self.log_result("Suggestion Apply Cross-Workspace Protection", False, "No suggestion A ID available")
            return False
        
        try:
            # Try to apply Workspace A suggestion with Workspace B header - should return 404
            response = requests.post(
                f"{self.api_url}/suggestions/{self.suggestion_a_id}/apply",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_result("Suggestion Apply Cross-Workspace Protection", False, f"SECURITY BREACH: Workspace B can apply Workspace A suggestion! Status: {response.status_code}")
                return False
            
            if response.status_code != 404:
                self.log_result("Suggestion Apply Cross-Workspace Protection", False, f"Expected 404, got {response.status_code}")
                return False
            
            self.log_result("Suggestion Apply Cross-Workspace Protection", True, "Workspace B cannot apply Workspace A suggestion (404)")
            return True
            
        except Exception as e:
            self.log_result("Suggestion Apply Cross-Workspace Protection", False, f"Error: {str(e)}")
            return False

    def test_suggestion_dismiss_cross_workspace_protection(self):
        """CRITICAL: Verify POST /api/suggestions/{id}/dismiss with wrong workspace header returns 404"""
        if not self.suggestion_b_id:
            self.log_result("Suggestion Dismiss Cross-Workspace Protection", False, "No suggestion B ID available")
            return False
        
        try:
            # Try to dismiss Workspace B suggestion with Workspace A header - should return 404
            response = requests.post(
                f"{self.api_url}/suggestions/{self.suggestion_b_id}/dismiss",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_result("Suggestion Dismiss Cross-Workspace Protection", False, f"SECURITY BREACH: Workspace A can dismiss Workspace B suggestion! Status: {response.status_code}")
                return False
            
            if response.status_code != 404:
                self.log_result("Suggestion Dismiss Cross-Workspace Protection", False, f"Expected 404, got {response.status_code}")
                return False
            
            self.log_result("Suggestion Dismiss Cross-Workspace Protection", True, "Workspace A cannot dismiss Workspace B suggestion (404)")
            return True
            
        except Exception as e:
            self.log_result("Suggestion Dismiss Cross-Workspace Protection", False, f"Error: {str(e)}")
            return False

    def test_performance_isolation_read(self):
        """CRITICAL: Verify GET /api/performance returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/performance",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Performance Isolation - Workspace A Query", False, f"Status: {response_a.status_code}")
                return False
            
            performance_a = response_a.json()
            perf_a_items = [perf.get('item_name', '') for perf in performance_a]
            
            # Check for leakage
            workspace_b_leaked = any("Workspace B Item" in name for name in perf_a_items)
            
            if workspace_b_leaked:
                self.log_result("Performance Isolation - Workspace A Query", False, f"DATA LEAK: Workspace B performance found in Workspace A query!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/performance",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Performance Isolation - Workspace B Query", False, f"Status: {response_b.status_code}")
                return False
            
            performance_b = response_b.json()
            perf_b_items = [perf.get('item_name', '') for perf in performance_b]
            
            # Check for leakage
            workspace_a_leaked = any("Workspace A Item" in name for name in perf_b_items)
            
            if workspace_a_leaked:
                self.log_result("Performance Isolation - Workspace B Query", False, f"DATA LEAK: Workspace A performance found in Workspace B query!")
                return False
            
            self.log_result("Performance Isolation - Read", True, f"Workspace A sees {len(performance_a)} performance records, Workspace B sees {len(performance_b)} records. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Performance Isolation - Read", False, f"Error: {str(e)}")
            return False

    def test_price_history_cross_workspace_protection(self):
        """CRITICAL: Verify GET /api/price-history/{item_id} with wrong workspace header returns empty"""
        try:
            # Try to access Workspace A item price history with Workspace B header
            response = requests.get(
                f"{self.api_url}/price-history/{self.item_a_id}",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result("Price History Cross-Workspace Protection", False, f"Expected 200, got {response.status_code}")
                return False
            
            data = response.json()
            
            # Should return empty list (no price history for this item in workspace B)
            if len(data) > 0:
                self.log_result("Price History Cross-Workspace Protection", False, f"DATA LEAK: Workspace B can see Workspace A price history! Count: {len(data)}")
                return False
            
            self.log_result("Price History Cross-Workspace Protection", True, "Workspace B cannot see Workspace A price history (empty list)")
            return True
            
        except Exception as e:
            self.log_result("Price History Cross-Workspace Protection", False, f"Error: {str(e)}")
            return False

    def test_performance_intelligence_isolation(self):
        """CRITICAL: Verify GET /api/performance-intelligence returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/performance-intelligence",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Performance Intelligence Isolation - Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            data_a = response_a.json()
            
            # Check all sections for leakage
            all_items_a = []
            for section in ['best_performing', 'worst_performing', 'needs_attention']:
                if section in data_a:
                    all_items_a.extend([item.get('name', '') for item in data_a[section]])
            
            workspace_b_leaked = any("Workspace B Item" in name for name in all_items_a)
            
            if workspace_b_leaked:
                self.log_result("Performance Intelligence Isolation - Workspace A", False, f"DATA LEAK: Workspace B data in Workspace A intelligence!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/performance-intelligence",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Performance Intelligence Isolation - Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            data_b = response_b.json()
            
            # Check all sections for leakage
            all_items_b = []
            for section in ['best_performing', 'worst_performing', 'needs_attention']:
                if section in data_b:
                    all_items_b.extend([item.get('name', '') for item in data_b[section]])
            
            workspace_a_leaked = any("Workspace A Item" in name for name in all_items_b)
            
            if workspace_a_leaked:
                self.log_result("Performance Intelligence Isolation - Workspace B", False, f"DATA LEAK: Workspace A data in Workspace B intelligence!")
                return False
            
            self.log_result("Performance Intelligence Isolation", True, "Both workspaces see only their own intelligence data. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Performance Intelligence Isolation", False, f"Error: {str(e)}")
            return False

    def test_market_signals_isolation(self):
        """CRITICAL: Verify GET /api/market/signals returns ONLY workspace-scoped data"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/market/signals",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Market Signals Isolation - Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            signals_a = response_a.json()
            signal_a_names = [signal.get('name', '') for signal in signals_a]
            
            workspace_b_leaked = any("Workspace B Item" in name for name in signal_a_names)
            
            if workspace_b_leaked:
                self.log_result("Market Signals Isolation - Workspace A", False, f"DATA LEAK: Workspace B signals in Workspace A query!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/market/signals",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Market Signals Isolation - Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            signals_b = response_b.json()
            signal_b_names = [signal.get('name', '') for signal in signals_b]
            
            workspace_a_leaked = any("Workspace A Item" in name for name in signal_b_names)
            
            if workspace_a_leaked:
                self.log_result("Market Signals Isolation - Workspace B", False, f"DATA LEAK: Workspace A signals in Workspace B query!")
                return False
            
            self.log_result("Market Signals Isolation", True, f"Workspace A sees {len(signals_a)} signals, Workspace B sees {len(signals_b)} signals. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Market Signals Isolation", False, f"Error: {str(e)}")
            return False

    def test_integrations_isolation(self):
        """CRITICAL: Verify GET /api/integrations returns ONLY workspace-scoped connectors"""
        try:
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/integrations",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Integrations Isolation - Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            integrations_a = response_a.json()
            
            # Each workspace should have its own set of connectors (5 default connectors)
            if len(integrations_a) != 5:
                self.log_result("Integrations Isolation - Workspace A", False, f"Expected 5 connectors, got {len(integrations_a)}")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/integrations",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Integrations Isolation - Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            integrations_b = response_b.json()
            
            if len(integrations_b) != 5:
                self.log_result("Integrations Isolation - Workspace B", False, f"Expected 5 connectors, got {len(integrations_b)}")
                return False
            
            self.log_result("Integrations Isolation", True, f"Both workspaces have their own 5 connectors. Isolation verified.")
            return True
            
        except Exception as e:
            self.log_result("Integrations Isolation", False, f"Error: {str(e)}")
            return False

    def test_inbox_isolation(self):
        """CRITICAL: Verify GET /api/inbox returns ONLY workspace-scoped messages"""
        try:
            # Refresh inbox for Workspace A
            requests.post(
                f"{self.api_url}/inbox/refresh",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            # Refresh inbox for Workspace B
            requests.post(
                f"{self.api_url}/inbox/refresh",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/inbox",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Inbox Isolation - Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            inbox_a = response_a.json()
            inbox_a_items = [msg.get('related_item_name', '') for msg in inbox_a]
            
            workspace_b_leaked = any("Workspace B Item" in name for name in inbox_a_items if name)
            
            if workspace_b_leaked:
                self.log_result("Inbox Isolation - Workspace A", False, f"DATA LEAK: Workspace B inbox message in Workspace A!")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/inbox",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Inbox Isolation - Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            inbox_b = response_b.json()
            inbox_b_items = [msg.get('related_item_name', '') for msg in inbox_b]
            
            workspace_a_leaked = any("Workspace A Item" in name for name in inbox_b_items if name)
            
            if workspace_a_leaked:
                self.log_result("Inbox Isolation - Workspace B", False, f"DATA LEAK: Workspace A inbox message in Workspace B!")
                return False
            
            self.log_result("Inbox Isolation", True, f"Workspace A sees {len(inbox_a)} messages, Workspace B sees {len(inbox_b)} messages. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Inbox Isolation", False, f"Error: {str(e)}")
            return False

    def test_brief_isolation(self):
        """CRITICAL: Verify GET /api/brief/latest returns ONLY workspace-scoped brief"""
        try:
            # Generate brief for Workspace A
            print("   ⏳ Generating brief for Workspace A (10-20s)...")
            requests.post(
                f"{self.api_url}/brief/generate",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=40
            )
            
            # Generate brief for Workspace B
            print("   ⏳ Generating brief for Workspace B (10-20s)...")
            requests.post(
                f"{self.api_url}/brief/generate",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=40
            )
            
            # Query with Workspace A header
            response_a = requests.get(
                f"{self.api_url}/brief/latest",
                headers={"X-Workspace-Id": self.workspace_a_id},
                timeout=10
            )
            
            if response_a.status_code != 200:
                self.log_result("Brief Isolation - Workspace A", False, f"Status: {response_a.status_code}")
                return False
            
            brief_a = response_a.json()
            if not brief_a:
                self.log_result("Brief Isolation - Workspace A", False, "No brief returned")
                return False
            
            # Query with Workspace B header
            response_b = requests.get(
                f"{self.api_url}/brief/latest",
                headers={"X-Workspace-Id": self.workspace_b_id},
                timeout=10
            )
            
            if response_b.status_code != 200:
                self.log_result("Brief Isolation - Workspace B", False, f"Status: {response_b.status_code}")
                return False
            
            brief_b = response_b.json()
            if not brief_b:
                self.log_result("Brief Isolation - Workspace B", False, "No brief returned")
                return False
            
            # Briefs should be different (different workspace_id)
            if brief_a.get('id') == brief_b.get('id'):
                self.log_result("Brief Isolation", False, f"DATA LEAK: Same brief returned for both workspaces!")
                return False
            
            self.log_result("Brief Isolation", True, "Each workspace has its own brief. No leakage.")
            return True
            
        except Exception as e:
            self.log_result("Brief Isolation", False, f"Error: {str(e)}")
            return False

    def test_header_missing_fallback(self):
        """Test missing X-Workspace-Id header falls back to default workspace"""
        try:
            # Query without header - should fall back to default workspace
            response = requests.get(f"{self.api_url}/items", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Header Missing - Fallback to Default", False, f"Status: {response.status_code}")
                return False
            
            items = response.json()
            
            self.log_result("Header Missing - Fallback to Default", True, f"Returned {len(items)} items from default workspace")
            return True
            
        except Exception as e:
            self.log_result("Header Missing - Fallback to Default", False, f"Error: {str(e)}")
            return False

    def test_header_invalid_fallback(self):
        """Test invalid X-Workspace-Id header falls back to default workspace"""
        try:
            # Query with invalid header - should fall back to default workspace
            response = requests.get(
                f"{self.api_url}/items",
                headers={"X-Workspace-Id": "invalid-workspace-id-12345"},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result("Header Invalid - Fallback to Default", False, f"Status: {response.status_code}")
                return False
            
            items = response.json()
            
            self.log_result("Header Invalid - Fallback to Default", True, f"Returned {len(items)} items from default workspace")
            return True
            
        except Exception as e:
            self.log_result("Header Invalid - Fallback to Default", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all workspace isolation tests"""
        print("=" * 80)
        print("LISTRIX MULTI-WORKSPACE DATA ISOLATION TESTS (P0 PRIORITY)")
        print(f"Testing: {self.base_url}")
        print("=" * 80)
        print()
        
        # Setup
        print("🔧 SETUP - Create Test Workspaces")
        if not self.test_create_workspaces():
            print("\n❌ CRITICAL: Failed to create test workspaces. Aborting.")
            return 1
        print()
        
        # Create test data
        print("📦 SETUP - Create Test Data in Both Workspaces")
        if not self.test_create_items_in_workspaces():
            print("\n❌ CRITICAL: Failed to create test items. Aborting.")
            return 1
        if not self.test_generate_listings_in_workspaces():
            print("\n❌ CRITICAL: Failed to generate listings. Aborting.")
            return 1
        if not self.test_analyze_items_in_workspaces():
            print("\n❌ CRITICAL: Failed to analyze items. Aborting.")
            return 1
        print()
        
        # Core isolation tests
        print("🔒 CRITICAL - READ ISOLATION TESTS")
        self.test_items_isolation_read()
        self.test_listings_isolation_read()
        self.test_events_isolation_read()
        self.test_suggestions_isolation_read()
        self.test_performance_isolation_read()
        self.test_performance_intelligence_isolation()
        self.test_market_signals_isolation()
        self.test_integrations_isolation()
        self.test_inbox_isolation()
        self.test_brief_isolation()
        print()
        
        # Cross-workspace mutation protection
        print("🛡️ CRITICAL - CROSS-WORKSPACE MUTATION PROTECTION")
        self.test_item_detail_cross_workspace_protection()
        self.test_analyze_cross_workspace_protection()
        self.test_suggestion_apply_cross_workspace_protection()
        self.test_suggestion_dismiss_cross_workspace_protection()
        self.test_price_history_cross_workspace_protection()
        print()
        
        # Header edge cases
        print("🔍 HEADER EDGE CASES")
        self.test_header_missing_fallback()
        self.test_header_invalid_fallback()
        print()
        
        # Summary
        print("=" * 80)
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} PASSED")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED - ZERO CROSS-WORKSPACE DATA LEAKAGE DETECTED")
            return 0
        else:
            failed = self.tests_run - self.tests_passed
            print(f"❌ {failed} TEST(S) FAILED - DATA ISOLATION ISSUES DETECTED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
            return 1

def main():
    tester = WorkspaceIsolationTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
