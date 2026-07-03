# API-SECURITY-TESTING-LAB
# crAPI Security Testing Lab

This repository documents my hands-on security testing work against the intentionally vulnerable **crAPI (Completely Ridiculous API)** application.

The goal of this project is to understand real-world API security issues by exploring authentication flows, object-level access, and common OWASP API vulnerabilities in a controlled lab environment.

---

## What this project demonstrates

Through this lab, I am practicing:

- API reconnaissance and workflow mapping
- Authentication and JWT-based session handling
- Object-level authorization analysis
- Identifying insecure API design patterns
- Writing professional security findings reports

This is part of my practical training in API security and bug bounty readiness.

---

## Lab Environment

- Application: crAPI (vulnerable API training platform)
- Local URL: http://localhost:8888
- Email testing: http://localhost:8025 (Mailhog)
- Interception tools: Burp Suite / Browser DevTools

---

## What I documented first

Before testing vulnerabilities, I documented the normal application behavior (happy path).

This helped me establish a baseline of how the system is supposed to work before identifying any security issues.

👉 Full Happy Path Documentation: [`happy-path.md`](./happy-path.md)

---

## Application Flow Overview

The normal user journey in crAPI is:

1. User Registration
2. Email / Token Verification
3. User Login (JWT issued)
4. Dashboard Access
5. Vehicle Creation
6. Vehicle Location Lookup
7. Interaction with community and workshop features

Each of these steps involves API calls that I inspected and documented.

---

## Key API Endpoints Observed

| Feature | Method | Endpoint |
|--------|--------|----------|
| User Signup | POST | `/identity/api/auth/signup` |
| User Login | POST | `/identity/api/auth/login` |
| Token Verification | POST | `/identity/api/auth/verify` |
| Add Vehicle | POST | `/workshop/api/vehicle` |
| Vehicle Location | GET | `/identity/api/v2/vehicle/{vehicleId}/location` |

---

## Security Focus Areas (Next Phase)

After mapping the application, I will begin testing for:

- Broken Object Level Authorization (BOLA)
- Broken Authentication issues
- Excessive Data Exposure
- JWT misconfiguration vulnerabilities
- Mass assignment issues
- Rate limiting weaknesses

These are aligned with the most common API security risks listed in the OWASP API Security Top 10.

---

## What I am building with this project

This is not just a lab exercise.

I am building a portfolio that demonstrates:

- Real API security testing skills
- Ability to understand system behavior before exploitation
- Structured vulnerability reporting
- Hands-on experience with industry-standard tools

---

## Next Steps

The next phase of this project will include:

- First BOLA exploitation (vehicle ID manipulation)
- Access control testing across users
- JWT attack simulation
- Writing full vulnerability reports with remediation steps
