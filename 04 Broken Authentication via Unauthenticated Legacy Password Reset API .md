# Broken Authentication via Legacy Password Reset API

## Why I looked here

After spending some time exploring crAPI, I decided to take a closer look at the password reset functionality.

Whenever I come across an OTP-based password reset flow, one of the first questions I ask myself is, **"What actually stops someone from guessing the OTP?"** A short OTP isn't automatically a vulnerability. Plenty of applications use four or six-digit codes securely because they're backed by protections like rate limiting, retry limits, or temporary account lockouts.

So instead of worrying about the length of the OTP, I wanted to see how well the verification endpoint was protected.

---


To start, I initiated a password reset using an email address I had already discovered during my earlier testing of the Community Forum.

The application generated a **4-digit OTP**, which had to be verified before I could change the password.

A four-digit OTP gives a search space of just **10,000 possible combinations (0000–9999)**. That's perfectly acceptable if the application makes repeated guesses difficult, so my next step was to see how it handled multiple verification attempts.

I started with the latest password reset endpoint.

```http
POST /identity/api/v3/password/reset
```

After a few incorrect OTP submissions, the application started rejecting my requests.

That was actually reassuring.

The endpoint was clearly enforcing rate limiting, making brute-force attempts unrealistic. At that point, I thought the password reset flow had been implemented properly.

---

## Then I noticed something interesting

While reviewing the available API endpoints, I spotted another version of the same functionality.

```http
POST /identity/api/v2/password/reset
```

I wasn't expecting much to change, but I repeated the same test anyway.

This time, the behaviour was completely different.

No matter how many incorrect OTPs I submitted, the endpoint continued accepting requests.

There were:

- No rate limits
- No delays between attempts
- No temporary account lockouts
- No indication that failed attempts were being tracked

That immediately stood out.

The newer API was protected, but the legacy endpoint wasn't.

Instead of breaking the protection on `v3`, all I had to do was switch to `v2`.

---

## Turning the observation into proof

At this point, I knew there was a weakness, but I wanted to find out whether it was actually exploitable.

My first attempt was with **Burp Suite Intruder**.

It worked, but the Community Edition was simply too slow to test all **10,000** possible OTPs within a reasonable time.

Rather than waiting, I decided to automate the process myself.

I wrote a small Python script that:

- Generated every possible four-digit OTP
- Sent verification requests automatically
- Used multithreading to improve performance
- Monitored responses for successful verification
- Stopped immediately after finding the correct OTP

The goal wasn't just to brute-force the OTP—it was to answer a simple question:

> **Could an attacker realistically abuse this endpoint?**

---

## What happened

The answer turned out to be **yes**.

The script successfully recovered the correct OTP in approximately **45 seconds**.

Using the recovered code, I completed the password reset process and successfully changed the account's password.

That was the moment the real issue became obvious.

The application had already solved the brute-force problem—but only in the latest API version.

By sending requests to the legacy endpoint instead, I was able to bypass those protections completely.


---

## Confirming it wasn't a one-off

Before documenting the finding, I wanted to make sure this wasn't caused by a single password reset request or a temporary issue.

I repeated the process several times.

Each time, the behaviour was exactly the same.

The `v3` endpoint consistently enforced rate limiting.

The `v2` endpoint consistently accepted unlimited OTP verification requests.

That confirmed this wasn't an isolated bug but a security control that had simply never been implemented on the legacy API.

---

## Why this matters

What makes this finding interesting isn't the fact that the OTP was only four digits long.

The real issue is the inconsistency between API versions.

The application correctly protected the latest password reset endpoint against brute-force attacks, but the legacy endpoint exposed the same functionality without those protections.

That means an attacker who knows a user's email address doesn't need to attack the protected endpoint.

They can simply interact with the older one instead.

In a real application, that could allow an attacker to recover the OTP, reset another user's password, and take over their account.

---

## Root cause

This finding comes down to inconsistent security controls across API versions.

The latest password reset endpoint enforced rate limiting.

The legacy endpoint didn't.

Both endpoints performed the same function, but only one applied the controls needed to protect OTP verification.

It's a good reminder that strengthening security in a new API version isn't enough if older versions remain accessible with weaker protections.

---

## How I'd fix it

Both API versions should enforce the same authentication controls.

At a minimum, the legacy endpoint should implement:

- Rate limiting
- Retry limits
- Temporary account lockouts
- Request throttling

If the legacy endpoint is no longer required, removing it entirely would be the safest option.

Security shouldn't depend on whether a client calls `v2` or `v3`.

---

## Evidence

During testing, I collected the following evidence:

- Password reset request
- Rate limiting observed on the `v3` endpoint
- Python automation script
- Successful OTP verification
- Successful password reset

---

## Where this fits

**OWASP API Security Top 10 (2023)**

- **API2:2023 – Broken Authentication**

---

## Lesson I'm taking forward

One thing I enjoyed about this finding is that it reminded me not to stop testing just because the first endpoint looked secure.

If I had only tested the latest API version, I probably would have concluded that the password reset process was well protected and moved on.

Instead, checking one older endpoint completely changed the outcome.

It's a good reminder that sometimes the easiest way around a security control isn't breaking it—it's finding another path where that control was never implemented.
