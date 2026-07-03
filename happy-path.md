# crAPI Happy Path


Before I go anywhere near breaking crAPI, I wanted to actually understand how it's *supposed* to work. It's easy to jump straight into throwing payloads at endpoints, but if I don't know what "normal" looks like, I won't recognize what's actually broken when I see it.

So this is basically me walking through the app end-to-end as a regular user would, signing up, verifying, logging in, poking around the dashboard, adding a vehicle and just paying attention to how the API responds at each step. Nothing offensive yet, just recon and baseline-building.

**Setup:** crAPI running locally on `localhost:8888`, Mailhog on `localhost:8025` for catching emails, and Burp sitting in the middle so I can see every request as it goes out.

---

## Step 1: Creating an account

First thing I did was hit the signup endpoint:

```
POST /identity/api/auth/signup
```

with a basic payload: name, email, phone number, password. Nothing fancy.

It came back clean:

```json
{
  "message": "User registered successfully! Please Login.",
  "status": 200
}
```

A couple things stood out right away, even at this early stage. There's no authentication needed to hit this endpoint (which is fine, it's signup, that's expected).

## Step 2: Verifying the account

Next up, verification. I expected this to be an email-code type flow, but crAPI actually does it with a JWT:

```
POST /identity/api/auth/verify
```

```json
{ "token": "eyJhbGciOiJSUzI1NiJ9...." }
```

Response:

```json
{
  "message": "The token is a valid JWT token",
  "status": 200
}
```

So the backend is just checking "is this a valid JWT" and calling it a day, it didn't even tell me explicitly what account state changed. That's a little interesting because it means the whole verification step is leaning entirely on trust in the JWT itself. If the JWT handling anywhere in this app turns out to be weak, this is one of the places that trust could get exploited.

## Step 3: Logging in

Standard login:

```
POST /identity/api/auth/login
```

```json
{
  "email": "muizrecon@apisecurity.com",
  "password": "A******@"
}
```

Got back a Bearer token:

```json
{
  "token": "eyJhbGciOiJSUzI1NiJ9....",
  "type": "Bearer",
  "message": "Login successful",
  "mfaRequired": false
}
```

No MFA, no session cookie auth here is 100% JWT-based. That's useful to know because it tells me every protected request from now on is going to be about that `Authorization: Bearer <token>` header, and if I ever want to test things like privilege escalation or BOLA, the JWT is the thing I'll be manipulating.

## Step 4: Checking the dashboard

With a valid token in hand, I hit:

```
GET /identity/api/v2/user/dashboard
```

and got my own user data back:

```json
{
  "id": 8,
  "name": "Abdulmuiz",
  "email": "muizrecon@apisecurity.com",
  "number": "*******7890",
  "available_credit": 100.0,
  "role": "ROLE_USER"
}
```

Straightforward! token gets accepted, I get my profile, and I can see my `role` sitting right there in the response as `ROLE_USER`. Filing that away, because anywhere a role or permission level shows up in a response is worth revisiting later.

## Step 5: Adding a vehicle

crAPI's whole theme is a connected-car app, so naturally there's a "register your vehicle" flow:

```
POST /identity/api/v2/vehicle/add_vehicle
```

```json
{
  "vin": "9ENWPB3*******YWHU",
  "pincode": "5****"
}
```

```json
{
  "message": "Vehicle save successfully..",
  "status": 200
}
```

Works exactly as you'd expect, authenticated request, VIN and pincode go in, vehicle gets tied to my account.

## Step 6: Pulling my vehicles back

Last step, just confirming I can read back what I created:

```
GET /identity/api/v2/vehicle/vehicles
```

```json
[
  {
    "id": 6,
    "uuid": "20106adb-9f87-4fdc-9cde-edb92c7e77b6",
    "vin": "9ENWPB3*******HU",
    "pincode": "5***",
    "year": 2026,
    "status": "INACTIVE",
    "model": {
      "model": "RS7",
      "vehiclecompany": { "name": "Audi" }
    },
    "vehicleLocation": {
      "latitude": "32.778889",
      "longitude": "-91.919243"
    }
  }
]
```

This response is actually one of the more interesting ones so far. It's returning both an internal numeric `id` *and* a `uuid`, plus nested model and location data, all in one blob. Two different identifier types on the same object is exactly the kind of thing that becomes relevant once I start testing object-level authorization, if the app uses the numeric ID somewhere else predictably, that's a much easier thing to enumerate than the UUID.

---

## Where this leaves me

Now that I've walked the full flow once, here's what I'm carrying forward into actual testing:

- **Auth is all JWT, no cookies, no MFA**: so most of my auth-bypass or privilege-escalation attempts are going to run through that token.
- **Verification trusts the JWT completely**: worth a closer look at the token structure/signature itself.
- **Role is exposed directly in the dashboard response**: good candidate for mass assignment or tampering checks later.
- **Vehicles have both an `id` and a `uuid`**:  if any endpoint uses the plain numeric ID, that's my first BOLA target.
- **No rate limiting spotted on signup or login yet**: keep this in mind for brute-force / enumeration testing.

Baseline done. Next step is starting to actually poke at these assumptions — starting with how object IDs are handled across endpoints.
