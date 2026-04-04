# MagicBricks API Integration

## Overview
This document describes the API integration for receiving leads from MagicBricks into the Legacy Hub CRM system.

## Endpoint Details

### Webhook URL
```
POST http://your-domain.com/webhook/magicbricks
```

### Authentication
- **Method**: API Key in Header
- **Header Name**: `API-Key`
- **API Key**: Set in `.env` file as `MAGIC_API`

### Request Headers
```
Content-Type: application/json
API-Key: YOUR_MAGIC_API_KEY
```

### Request Body
The endpoint expects JSON data with the following structure:

```json
{
  "name": "Himanshu Kumar",
  "state": "Rajasthan",
  "city": "Jaipur",
  "location": "GK Colony",
  "budget": "5403192",
  "notes": "comments",
  "email": "",
  "countryCode": "91",
  "mobile": "9988776655",
  "project": "Aamor",
  "property": "Villa",
  "leadExpectedBudget": "6000000",
  "propertyType": "Flat",
  "propertySubType": "Plot",
  "submittedDate": "28-03-18",
  "submittedTime": "22:22:32",
  "subsource": "",
  "leadStatus": "Schedule Site Visit or Schedule Meeting or Booked or Booking Cancel",
  "callRecordingUrl": "",
  "leadScheduledDate": "28-03-18",
  "leadScheduleTime": "22:22:32",
  "bhkType": "Simplex/Duplex/PentHouse/Others",
  "leadBookedDate": "28-03-18",
  "leadBookedTime": "22:22:32",
  "additionalProperties": {
    "EnquiredFor": "Buy/Sale/Rent",
    "BHKType": "Simplex/Duplex/PentHouse/Others",
    "NoOfBHK": "0",
    "key1": "value1",
    "key2": "value1"
  },
  "primaryUser": "Rahul N",
  "secondaryUser": "Ranjan Gupta"
}
```

### Required Fields
- `name` (string): Lead name
- `mobile` (string): Mobile number

### Processing Logic

#### Success Case
1. Validates required fields (name, mobile)
2. Creates or finds "MagicBricks" source in database
3. Assigns lead to sales person with minimum queries
4. Creates new query in the system
5. Stores webhook data for audit trail
6. Returns success response

#### Error Case
1. If validation fails or processing error occurs
2. Stores complete JSON payload in `webhook_data` table
3. Marks as `is_processed = false`
4. Includes error message for debugging
5. Returns error response

### Response Format

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Query created successfully with ID: 123"
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Missing required field: mobile"
}
```

### Environment Setup
Add the following to your `.env` file:
```
MAGIC_API=your_magicbricks_api_key_here
```

### Database Tables Used
- `queries`: Stores successfully processed leads
- `sources`: Source information (creates "MagicBricks" if not exists)
- `webhook_data`: Audit trail for all webhook attempts

### Error Handling
- Invalid API key returns 400 error
- Missing required fields returns 400 error
- Server errors are logged and webhook data is saved
- All failed attempts are stored for manual review

### Testing
Use curl to test the endpoint:
```bash
curl --location --request POST http://localhost:8000/webhook/magicbricks \
--header "API-Key: YOUR_MAGIC_API_KEY" \
--header "Content-Type: application/json" \
--data '{
  "name": "Test User",
  "mobile": "9876543210",
  "email": "test@example.com"
}'
```

### Monitoring
Check the `webhook_data` table for:
- Failed processing attempts
- Error messages
- Raw payload data for debugging

### Integration Notes
- The endpoint follows the same data structure as 99acres for consistency
- All additional properties in the JSON are stored in the webhook data table
- Phone numbers are combined with country code if provided
- Leads are automatically assigned to the sales person with the least number of active queries
