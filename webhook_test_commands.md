# Webhook Test Commands

## Setup
Add your API keys to environment variables or replace in commands below:
```bash
export ACRES_API="your_99acres_api_key_here"
export MAGIC_API="your_magicbricks_api_key_here"
```

## 99acres Tests

### 1. Valid Lead
```bash
curl --location --request POST http://localhost:8000/webhook/99acres \
--header "Content-Type: application/json" \
--header "API-Key: your_99acres_api_key_here" \
--data '{
  "name": "Himanshu Kumar",
  "state": "Rajasthan",
  "city": "Jaipur",
  "location": "GK Colony",
  "budget": "5403192",
  "notes": "Test lead from 99acres",
  "email": "himanshu@example.com",
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
  "leadStatus": "Schedule Site Visit",
  "callRecordingUrl": "",
  "leadScheduledDate": "28-03-18",
  "leadScheduleTime": "22:22:32",
  "bhkType": "Simplex",
  "leadBookedDate": "28-03-18",
  "leadBookedTime": "22:22:32",
  "additionalProperties": {
    "EnquiredFor": "Buy",
    "BHKType": "Simplex",
    "NoOfBHK": "3"
  },
  "primaryUser": "Rahul N",
  "secondaryUser": "Ranjan Gupta"
}'
```

### 2. Missing Required Field (no name)
```bash
curl --location --request POST http://localhost:8000/webhook/99acres \
--header "Content-Type: application/json" \
--header "API-Key: your_99acres_api_key_here" \
--data '{
  "state": "Rajasthan",
  "city": "Jaipur",
  "email": "test@example.com",
  "countryCode": "91",
  "mobile": "9988776655"
}'
```

### 3. Invalid API Key
```bash
curl --location --request POST http://localhost:8000/webhook/99acres \
--header "Content-Type: application/json" \
--header "API-Key: invalid_key" \
--data '{
  "name": "Test User",
  "mobile": "9876543210"
}'
```

## MagicBricks Tests

### 1. Valid Lead
```bash
curl --location --request POST http://localhost:8000/webhook/magicbricks \
--header "Content-Type: application/json" \
--header "API-Key: your_magicbricks_api_key_here" \
--data '{
  "name": "Priya Sharma",
  "state": "Maharashtra",
  "city": "Mumbai",
  "location": "Bandra West",
  "budget": "7500000",
  "notes": "Test lead from MagicBricks",
  "email": "priya@example.com",
  "countryCode": "91",
  "mobile": "9876543210",
  "project": "Skyline Towers",
  "property": "Apartment",
  "leadExpectedBudget": "8000000",
  "propertyType": "Flat",
  "propertySubType": "2BHK",
  "submittedDate": "29-03-18",
  "submittedTime": "15:30:45",
  "subsource": "Website",
  "leadStatus": "Interested",
  "callRecordingUrl": "",
  "leadScheduledDate": "30-03-18",
  "leadScheduleTime": "11:00:00",
  "bhkType": "Simplex",
  "leadBookedDate": "",
  "leadBookedTime": "",
  "additionalProperties": {
    "EnquiredFor": "Buy",
    "BHKType": "Simplex",
    "NoOfBHK": "2",
    "PreferredFloor": "Mid"
  },
  "primaryUser": "Amit Kumar",
  "secondaryUser": "Sneha Patel"
}'
```

### 2. Missing Required Field (no mobile)
```bash
curl --location --request POST http://localhost:8000/webhook/magicbricks \
--header "Content-Type: application/json" \
--header "API-Key: your_magicbricks_api_key_here" \
--data '{
  "name": "Test User",
  "email": "test@example.com",
  "city": "Delhi"
}'
```

### 3. Invalid API Key
```bash
curl --location --request POST http://localhost:8000/webhook/magicbricks \
--header "Content-Type: application/json" \
--header "API-Key: wrong_magic_key" \
--data '{
  "name": "Test User",
  "mobile": "9876543210"
}'
```

## Expected Responses

### Success (200 OK)
```json
{
  "success": true,
  "message": "Query created successfully with ID: 123"
}
```

### Error (400 Bad Request)
```json
{
  "success": false,
  "message": "Missing required field: mobile"
}
```

## Testing Steps

1. **Start the server**: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

2. **Test valid leads**: Run the valid lead commands for both endpoints
   - Should return 200 OK
   - Check admin panel for new queries
   - Check webhook review section for processed entries

3. **Test error cases**: Run commands with missing fields/invalid keys
   - Should return 400 Bad Request
   - Check webhook review section for failed entries with error messages

4. **Manual Review**: 
   - Go to Admin → Webhook Review
   - Filter by source (99acres/MagicBricks)
   - Filter by status (processed/failed)
   - Click "View" to see full JSON data
   - Click "Reprocess" to retry failed entries

## Environment Setup

Add to your `.env` file:
```
ACRES_API=your_99acres_api_key_here
MAGIC_API=your_magicbricks_api_key_here
```
