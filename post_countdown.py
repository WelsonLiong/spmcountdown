from __future__ import annotations

import argparse
from datetime import date, datetime
import os
from pathlib import Path
import sys
import time
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth1

load_dotenv()

TARGET_DATE = date(2026, 11, 23)
TIMEZONE = ZoneInfo("Asia/Kuala_Lumpur")
ENABLE_TWITTER = os.getenv("ENABLE_TWITTER", "false").lower() in ("true", "1", "yes")
ENABLE_THREADS = os.getenv("ENABLE_THREADS", "true").lower() in ("true", "1", "yes")


def get_days_remaining(current_date: Optional[date] = None) -> int:
    if current_date is None:
        current_date = datetime.now(TIMEZONE).date()
    return (TARGET_DATE - current_date).days


def get_captions(days_left: int) -> tuple[str, str]:
    if days_left > 1:
        twitter_text = f"{days_left} days left until #SPM2026"
        threads_text = f"{days_left} days left until SPM 2026"
    elif days_left == 1:
        twitter_text = "1 day left until #SPM2026"
        threads_text = "1 day left until SPM 2026"
    else:
        twitter_text = "Today is the day! Good luck to all candidates for #SPM2026"
        threads_text = "Today is the day! Good luck to all candidates for SPM 2026"
    return twitter_text, threads_text


def get_image_path(days_left: int, base_dir: Path) -> Path:
    image_file = base_dir / "images" / f"{days_left}.png"
    return image_file


def get_public_image_url(days_left: int) -> str:
    github_repo = os.getenv("GITHUB_REPOSITORY", "WelsonLiong/spmcountdown")
    github_branch = os.getenv("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{github_repo}/{github_branch}/images/{days_left}.png"


def refresh_threads_token(current_token: str) -> dict:
    print("\n--- [Meta Threads Token Refresh] ---")
    url = "https://graph.threads.com/refresh_access_token"
    params = {
        "grant_type": "th_refresh_token",
        "access_token": current_token,
    }
    resp = requests.get(url, params=params, timeout=30)
    if not resp.ok:
        print(f"Token refresh failed: {resp.status_code} - {resp.text}", file=sys.stderr)
        resp.raise_for_status()

    data = resp.json()
    new_token = data.get("access_token")
    expires_in = data.get("expires_in")
    print(f"Token refreshed successfully! Expires in: {expires_in} seconds.")

    if new_token:
        print(f"::add-mask::{new_token}")

    return data


def update_local_env(env_file: Path, new_token: str) -> None:
    try:
        content = env_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("THREADS_ACCESS_TOKEN="):
                new_lines.append(f"THREADS_ACCESS_TOKEN={new_token}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"THREADS_ACCESS_TOKEN={new_token}")
        env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print("Updated THREADS_ACCESS_TOKEN in local .env file.")
    except Exception as e:
        print(f"Note: Could not update local .env file: {e}")


def post_to_twitter(image_path: Path, caption: str, dry_run: bool = False) -> Optional[str]:
    print("\n--- [Twitter / X] ---")
    print(f"Caption: {caption}")
    print(f"Image: {image_path}")

    if dry_run:
        print("[DRY-RUN] Twitter post skipped.")
        return "dry-run-tweet-id"

    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    missing = [
        name
        for name, val in [
            ("TWITTER_API_KEY", api_key),
            ("TWITTER_API_SECRET", api_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret),
        ]
        if not val
    ]
    if missing:
        raise ValueError(f"Missing Twitter credentials in environment: {', '.join(missing)}")

    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

    print("Uploading media to Twitter v1.1...")
    with open(image_path, "rb") as img_file:
        upload_resp = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files={"media": img_file},
            timeout=60,
        )

    if not upload_resp.ok:
        print(f"Media upload failed: {upload_resp.status_code} - {upload_resp.text}")
        upload_resp.raise_for_status()

    media_id_str = upload_resp.json().get("media_id_string")
    print(f"Uploaded media ID: {media_id_str}")

    print("Posting tweet via Twitter v2...")
    tweet_payload = {
        "text": caption,
        "media": {"media_ids": [media_id_str]},
    }
    tweet_resp = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json=tweet_payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if not tweet_resp.ok:
        print(f"Tweet post failed: {tweet_resp.status_code} - {tweet_resp.text}")
        tweet_resp.raise_for_status()

    tweet_data = tweet_resp.json()
    tweet_id = tweet_data.get("data", {}).get("id")
    print(f"Successfully posted Tweet! ID: {tweet_id}")
    return tweet_id


def post_to_threads(image_url: str, caption: str, dry_run: bool = False) -> Optional[str]:
    print("\n--- [Meta Threads] ---")
    print(f"Caption: {caption}")
    print(f"Image URL: {image_url}")

    if dry_run:
        print("[DRY-RUN] Threads post skipped.")
        return "dry-run-threads-id"

    access_token = os.getenv("THREADS_ACCESS_TOKEN")
    user_id = os.getenv("THREADS_USER_ID") or "me"

    if not access_token:
        raise ValueError("Missing THREADS_ACCESS_TOKEN in environment.")

    print("Creating Threads media container...")
    container_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    container_params = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": caption,
        "access_token": access_token,
    }

    container_resp = requests.post(container_url, data=container_params, timeout=30)
    if not container_resp.ok:
        print(f"Container creation failed: {container_resp.status_code} - {container_resp.text}")
        container_resp.raise_for_status()

    container_id = container_resp.json().get("id")
    print(f"Created container ID: {container_id}")

    print("Waiting 15 seconds for Meta to process media container...")
    time.sleep(15)

    print("Publishing Threads post...")
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    publish_params = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    publish_resp = requests.post(publish_url, data=publish_params, timeout=30)
    if not publish_resp.ok:
        print(f"Publish failed: {publish_resp.status_code} - {publish_resp.text}")
        publish_resp.raise_for_status()

    threads_post_id = publish_resp.json().get("id")
    print(f"Successfully posted to Threads! Post ID: {threads_post_id}")
    return threads_post_id


def main() -> int:
    parser = argparse.ArgumentParser(description="SPM 2026 Countdown Auto-Poster")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without posting")
    parser.add_argument("--date", type=str, help="Simulate a specific date (YYYY-MM-DD)")
    parser.add_argument("--refresh-token", action="store_true", help="Force refresh Threads access token")
    parser.add_argument("--skip-twitter", action="store_true", help="Skip posting to Twitter")
    parser.add_argument("--skip-threads", action="store_true", help="Skip posting to Threads")
    args = parser.parse_args()

    if args.date:
        current_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        current_date = datetime.now(TIMEZONE).date()

    days_left = get_days_remaining(current_date)
    print(f"Date: {current_date} ({TIMEZONE.key})")
    print(f"SPM 2026 Date: {TARGET_DATE}")
    print(f"Days Remaining: {days_left}")

    if days_left > 100:
        print(f"Countdown has not started yet ({days_left} days remaining > 100). Exiting gracefully.")
        return 0

    if days_left < 0:
        print(f"SPM 2026 has already passed on {current_date}.")
        return 0

    base_dir = Path(__file__).resolve().parent

    if days_left == 50 or args.refresh_token:
        print(f"\n[Trigger] Day {days_left} reached or --refresh-token requested.")
        current_token = os.getenv("THREADS_ACCESS_TOKEN")
        if not current_token:
            print("Warning: THREADS_ACCESS_TOKEN not found in environment; skipping token refresh.", file=sys.stderr)
        elif args.dry_run:
            print("[DRY-RUN] Threads token refresh call simulated.")
        else:
            try:
                refresh_data = refresh_threads_token(current_token)
                new_token = refresh_data.get("access_token")
                if new_token:
                    os.environ["THREADS_ACCESS_TOKEN"] = new_token
                    update_local_env(base_dir / ".env", new_token)
                    github_output = os.getenv("GITHUB_OUTPUT")
                    if github_output:
                        with open(github_output, "a", encoding="utf-8") as out:
                            out.write(f"refreshed_threads_token={new_token}\n")
            except Exception as exc:
                print(f"Warning: Failed to refresh Threads token: {exc}", file=sys.stderr)

    image_path = get_image_path(days_left, base_dir)
    if not image_path.exists():
        print(f"Error: Countdown image not found at {image_path}", file=sys.stderr)
        return 1

    twitter_caption, threads_caption = get_captions(days_left)

    success = True

    if ENABLE_TWITTER and not args.skip_twitter:
        try:
            post_to_twitter(image_path, twitter_caption, dry_run=args.dry_run)
        except Exception as exc:
            print(f"Failed to post to Twitter: {exc}", file=sys.stderr)
            success = False

    if ENABLE_THREADS and not args.skip_threads:
        try:
            public_image_url = get_public_image_url(days_left) if not args.dry_run else f"https://example.com/images/{days_left}.png"
            post_to_threads(public_image_url, threads_caption, dry_run=args.dry_run)
        except Exception as exc:
            print(f"Failed to post to Threads: {exc}", file=sys.stderr)
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
