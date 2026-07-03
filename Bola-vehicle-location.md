# BOLA on the Vehicle Location Endpoint (via Forum Enumeration)

## Why I looked here

After mapping out the normal user flow in crAPI, one thing stuck with me from that recon: vehicles come back with both a plain numeric `id` and a `uuid`. Whenever I see a predictable-looking identifier sitting next to sensitive data, that's usually the first thing worth poking at for object-level authorization issues. Location data felt like the highest-value target if this were a real product, someone's real-time whereabouts leaking to a stranger is about as bad as it gets.

My first pass at this was pretty crude: I just guessed at another vehicle ID and dropped it into the request. It worked, but it bugged me that the "discovery" step relied on luck rather than something I could actually demonstrate as a repeatable path. So I went looking for a cleaner way to get a valid vehicle ID that belonged to someone else and the forum gave me exactly that.

## Finding the real discovery path

crAPI has a community/forum feature, and while poking around it I hit:

```
GET /community/api/v2/community/posts/recent?limit=30&offset=0
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWI*********************VjdXJpdHkuY29tIiwiaWF0IjoxNzgzMDYzMzExLCJleHAiOjE3ODM2NjgxMTEsInJvbGUiOiJ1c2VyIn0.aDHQ7cZj3zz8v-bXompogvpewEUnERQ8**********************************************************U20Muruao1Y0UQIc-5T6vweZ_JJFzfH6zx2Sgsz9hhYJl6pxlwROphi9KRR
```

The response was just recent forum posts — nothing unusual on the surface. But nested inside every single post's `author` object was this:

```json
"author": {
  "nickname": "Pogba",
  "email": "pogba006@example.com",
  "vehicleid": "cd515c12-0fc1-48ae-8b61-9230b70a845b",
  ...
}
```
[Community Vehicle IDs](../screenshots/community-vehicle-ids.png)

That stopped me. This is a forum endpoint, its job is to show posts. It has no business handing out another user's internal vehicle UUID alongside their real name and email. But there it was, for every author, on every post, just by having a valid token. No special permissions, no digging, it's returned by default.

That's a much stronger finding than guessing an ID. It means an attacker doesn't need to brute-force anything, the app itself hands you a mapping of *identity → vehicle ID* for free.

## Chaining it into the BOLA

I took the `vehicleid` for "Pogba" straight out of that forum response and dropped it into the vehicle location endpoint I'd already been testing:

```
GET /identity/api/v2/vehicle/cd515c12-0fc1-48ae-8b61-9230b70a845b/location
Authorization: Bearer  eyJhbGciOiJSUzI1NiJ9.eyJzdWI*********************VjdXJpdHkuY29tIiwiaWF0IjoxNzgzMDYzMzExLCJleHAiOjE3ODM2NjgxMTEsInJvbGUiOiJ1c2VyIn0.aDHQ7cZj3zz8v-bXompogvpewEUnERQ8**********************************************************U20Muruao1Y0UQIc-5T6vweZ_JJFzfH6zx2Sgsz9hhYJl6pxlwROphi9KR
```

And got this back:

```json
{
  "carId": "cd515c12-0fc1-48ae-8b61-9230b70a845b",
  "vehicleLocation": {
    "id": 2,
    "latitude": "31.284788",
    "longitude": "-92.471176"
  },
  "fullName": "Pogba",
  "email": "pogba006@example.com"
}
```

[Modified Request and Response](../screenshots/modified-request-response.png)

My token, someone else's vehicle ID, and the API just handed back their live coordinates along with their name and email, again, no ownership check at all.

## Confirming it's not a one-off

Before writing this up I wanted to be sure this wasn't a fluke tied to one particular account. I pulled the `vehicleid` for the other authors in that same forum response ("Robot" and "Adam") and ran the same request against each one. Same result every time — full name, email, and live location handed over for every account I tested, using nothing but my own authenticated token.

So this isn't a one-off misconfiguration on a single object. It's a systemic gap: the location endpoint never checks whether the vehicle in the URL actually belongs to the person making the request.

## Why this matters

This is a **Broken Object Level Authorization** issue, and it's compounded by an information disclosure problem sitting right next to it. Two things are going wrong at once:

- The forum endpoint leaks an internal object identifier (`vehicleid`) tied to real user identity, when it has no reason to expose that at all.
- The location endpoint trusts that identifier completely, without ever checking whether it belongs to the caller.

Put together, any authenticated user can go from "browsing the forum" to "here's this named individual's live GPS location" in two requests. In a real deployment, that's not a hypothetical, that's a stalking and physical-safety risk, not just a data leak on paper.

## Root cause

Two separate failures stacked on top of each other:

1. **Over-exposure of internal identifiers**: the community/posts endpoint returns a `vehicleid` field that has no business being in a public-facing forum response.
2. **Missing ownership validation**: the location endpoint accepts any `vehicleId` and returns data for it, without ever checking it against the authenticated user's own vehicles.

Neither of these alone would be as serious. Together, they form a complete, repeatable attack chain.

## How I'd fix it

Both layers need to be addressed:

**On the forum endpoint**, strip `vehicleid` (and honestly, probably `email` too) out of the public author object. A nickname and profile picture is plenty for a forum post; there's no reason to expose internal foreign keys tied to a user's other data.

**On the location endpoint**: enforce ownership check before returning anything:

```pseudo
if vehicle.owner_id != authenticated_user.id:
    return 403 Forbidden
```

The broader lesson: authorization has to be checked at the object level on *every* endpoint that accepts an ID, regardless of where that ID could plausibly have come from. "The ID is hard to guess" was never a real control here — the app was giving it away itself.

## Where this fits

This maps to **API1:2023 – Broken Object Level Authorization** in the OWASP API Security Top 10, with a secondary **API3:2023 – Broken Object Property Level Authorization** angle on the forum endpoint over-exposing fields it shouldn't.

---

**Lesson I'm taking forward:** the most useful ID for an attack isn't necessarily the one you can guess, it's the one the application accidentally hands you somewhere unrelated. Any time I see an internal-looking identifier (UUID, foreign key, anything ending in `id`) show up in a response where it doesn't obviously belong, that's worth chasing down to see what else it unlocks.
