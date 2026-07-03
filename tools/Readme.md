## BOLA Scanner ##

A small script I built to automate the BOLA finding documented in `Bola-vehicle-location.md`, instead of testing each vehicle by hand.

**What it does:**

1. Pulls every post from the community/forum endpoint (paginating through all of them, not just the first page)
2. Pulls out each author's `vehicleid` from the post data
3. Tries the vehicle location endpoint with each ID
4. Logs which ones return location data that isn't yours
5. Saves results to a timestamped JSON file if anything vulnerable is found

**Running it:**

```bash
cd tools
pip install -r requirements.txt
python3 bola-scanner.py
```

On first run it'll ask you to paste your JWT token and save it to `token.txt` for next time. That file is gitignored — don't commit it.

**Sample run against crAPI:**

```
target: http://localhost:8888
fetching forum posts...
found 3 posts
extracted 3 unique vehicle ids
[1/3] testing Robot (4bae9968...)
  vulnerable - got location for robot001@example.com
[2/3] testing Pogba (cd515c12...)
  vulnerable - got location for pogba006@example.com
[3/3] testing Adam (f89b5f21...)
  vulnerable - got location for adam007@example.com

tested: 3  vulnerable: 3  secure: 0
results saved to bola_scan_results_20260703_120134.json
```

**How it decides "vulnerable":** a hit only counts if the response is a 200 with a `vehicleLocation` object and the `carId` in the response matches the ID that was requested. That's deliberately checking for specific fields like an email address in the response is fragile if the API's schema ever changes, but a matching `carId` on a 200 is direct proof you got data back for an ID that isn't yours.

**Note on the "secure" count:** every vehicle ID this script has been tested against so far came back vulnerable, so the "secure" branch hasn't actually been exercised against a real record yet, only against IDs that don't exist at all. Worth keeping in mind if you're reading the output: right now, "secure: 0" reflects the state of this specific crAPI instance, not confirmation that the detection logic correctly identifies a properly-protected vehicle. That's still an open thing I'm looking into.

**Stack:** Python 3, `requests`. Nothing else required.

## License
 
This is a personal learning project, everything here was tested against a local, intentionally vulnerable lab (OWASP crAPI)training environment, never against systems I don't own or have explicit permission to test.
 
Feel free to read through the write-ups or reuse the scanner for your own lab testing.
