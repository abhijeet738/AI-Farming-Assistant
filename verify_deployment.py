#!/usr/bin/env python3
"""
Deployment Verification Script for HF Spaces

This script tests the deployed API endpoints to ensure everything is working correctly.
Run this after deployment to verify the system is operational.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Update this URL to your actual HF Space URL
BASE_URL = "https://abhijeetraj-farming-assistant-backend.hf.space"

async def test_endpoint(client: httpx.AsyncClient, method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = await client.get(url, timeout=30.0)
        elif method.upper() == "POST":
            response = await client.post(url, json=data, timeout=30.0)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}
        
        return {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text[:200]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def main():
    """Run deployment verification tests"""
    print("🚀 Starting HF Spaces Deployment Verification")
    print(f"🌐 Testing: {BASE_URL}")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        tests = [
            # Basic health checks
            ("GET", "/ping", None),
            ("GET", "/api/v1/health", None),
            ("GET", "/", None),
            
            # Weather API (should work without auth)
            ("GET", "/api/v1/weather/Maharashtra", None),
            
            # ML Model endpoints (test with sample data)
            ("POST", "/api/v1/crop/recommend", {
                "nitrogen": 90, "phosphorus": 42, "potassium": 43,
                "temperature": 28.5, "humidity": 78, "ph": 6.5, "rainfall": 45
            }),
            
            ("POST", "/api/v1/yield/predict", {
                "crop": "Rice", "state": "Maharashtra", "district": "Pune",
                "season": "Kharif", "area_hectares": 2.5
            }),
            
            ("POST", "/api/v1/fertilizer/recommend", {
                "crop": "Rice", "soil_type": "Clay", "nitrogen": 20, "phosphorus": 15, "potassium": 10
            }),
            
            ("GET", "/api/v1/market/rice", None),
            
            ("POST", "/api/v1/pest/risk", {
                "crop": "Rice", "location": "Maharashtra", "growth_stage": "flowering"
            }),
            
            # Chat endpoint (basic test)
            ("POST", "/api/v1/chat/invoke", {
                "message": "What is the best time to plant rice in Maharashtra?",
                "user_id": "test_user"
            })
        ]
        
        results = []
        for method, endpoint, data in tests:
            print(f"🧪 Testing {method} {endpoint}...")
            result = await test_endpoint(client, method, endpoint, data)
            results.append((endpoint, result))
            
            if result["status"] == "success":
                print(f"✅ {endpoint} - Status: {result['status_code']}")
            else:
                print(f"❌ {endpoint} - Error: {result.get('message', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 60)
        
        success_count = sum(1 for _, result in results if result["status"] == "success")
        total_count = len(results)
        
        print(f"✅ Successful: {success_count}/{total_count}")
        print(f"❌ Failed: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("\n🎉 ALL TESTS PASSED! Deployment is successful!")
        elif success_count >= total_count * 0.8:
            print("\n⚠️  Most tests passed. Check failed endpoints.")
        else:
            print("\n🚨 Multiple failures detected. Check deployment logs.")
        
        # Print detailed results for failed tests
        failed_tests = [(endpoint, result) for endpoint, result in results if result["status"] != "success"]
        if failed_tests:
            print("\n🔍 FAILED TEST DETAILS:")
            for endpoint, result in failed_tests:
                print(f"  {endpoint}: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())