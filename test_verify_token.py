import requests
import json
import sys

# Configuration - replace with your actual values
AUTH_SERVICE_URL = "http://localhost:5000"  # Change to your actual auth service URL
API_KEY = "niggas123"       # Replace with your actual API key
TOKEN_TO_VERIFY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiaWF0IjoxNzQyMDQ1MDI2LCJleHAiOjE3NDIxMzE0MjYsImF1ZCI6InRlc3QuZXhhbXBsZS5jb20ifQ.otT2ksKXdfWm5LU8Oa2m5VQ0UTcmLoQQ9utSKdiWqhI"    # Replace with the token you want to verify

def verify_token(token):
    """
    Verify a token with the authentication service
    
    Args:
        token (str): The token to verify
        
    Returns:
        dict: The response from the authentication service
    """
    endpoint = f"{AUTH_SERVICE_URL}/api/verify-token"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "token": token
    }
    
    try:
        # Send POST request to the verify-token endpoint
        response = requests.post(endpoint, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }

if __name__ == "__main__":
    # Use command line argument as token if provided
    if len(sys.argv) > 1:
        TOKEN_TO_VERIFY = sys.argv[1]
    
    print(f"Verifying token: {TOKEN_TO_VERIFY[:10]}...")
    
    result = verify_token(TOKEN_TO_VERIFY)
    
    if result["success"]:
        print("\n[SUCCESS] Token verification successful!")
        print("\nUser information:")
        print(json.dumps(result["data"]["user"], indent=4))
    else:
        print("\n[FAILED] Token verification failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if "status_code" in result:
            print(f"Status code: {result['status_code']}")
