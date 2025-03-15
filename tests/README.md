
# Test Service for Crafteri Auth

This test service demonstrates how a third-party application can integrate with Crafteri Auth for Single Sign-On (SSO).

## How It Works

1. User clicks "Login with Crafteri" on the test service
2. User is redirected to Crafteri Auth for authentication
3. After successful login, user is redirected back to the test service with a token
4. Test service verifies the token with Crafteri Auth
5. If valid, test service creates a local user account and session

## Database Structure

The test service uses two tables in the same database as Crafteri Auth:

- `testserviceusers` - Stores user information from Crafteri Auth
- `testservicetokens` - Stores session tokens for authenticated users

## Setup Instructions

### 1. Register the Test Service

Make sure the test service is registered in your Crafteri Auth's `registered_services` table:

