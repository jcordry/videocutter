#!/usr/bin/env python3
"""
Download a Panopto session as MP4 using OAuth2 + legacyLogin.

Prereqs:
  - An OAuth2 client in Panopto that can obtain a user-scoped token (e.g., User-Based Server Application).
  - A user with permission to download the session's podcast.
"""

import argparse
import os
import sys
import requests

def get_oauth_token_password_grant(server, client_id, client_secret, username, password, verify_ssl=True):
    """
    Obtain an access token via the Resource Owner Password Credentials (password) grant.
    This grant must be enabled/allowed by your Panopto setup. Otherwise, use an interactive flow and
    persist a refresh token, then swap to an access token before calling legacyLogin.

    Docs:
      - OAuth2 for services & client types in Panopto support
    """
    token_url = f"https://{server}/Panopto/oauth2/connect/token"
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "openid api offline_access"
    }
    resp = requests.post(token_url, data=data, auth=(client_id, client_secret), verify=verify_ssl)
    if resp.status_code != 200:
        raise RuntimeError(f"Token request failed [{resp.status_code}]: {resp.text}")
    return resp.json()["access_token"]

def legacy_login_with_cookie(server, access_token, session: requests.Session, verify_ssl=True):
    """
    Exchange OAuth2 Bearer token for a legacy auth cookie usable against web endpoints.
    The cookie is set on the provided requests.Session.
    """
    url = f"https://{server}/Panopto/api/v1/auth/legacyLogin"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = session.get(url, headers=headers, allow_redirects=False, verify=verify_ssl)
    if r.status_code // 100 != 2:
        raise RuntimeError(f"legacyLogin failed [{r.status_code}]: {r.text}")
    # Cookies are in session now (Set-Cookie). Nothing else to return.

def download_podcast_mp4(server, session_id, out_path, session: requests.Session, verify_ssl=True):
    """
    Download the "podcast" MP4 for the given session ID.
    This uses the same endpoint the UI calls (requires that podcast downloads are allowed).
    """
    # You can add &filename=<name>.mp4 if you want to force a filename
    url = f"https://{server}/Panopto/Podcast/Download/{session_id}.mp4?mediaTargetType=videoPodcast"

    with session.get(url, stream=True, verify=verify_ssl) as r:
        if r.status_code == 403:
            raise PermissionError("403 Forbidden: podcast download is disabled or your account lacks permission.")
        if r.status_code == 404:
            raise FileNotFoundError("404 Not Found: check the session ID.")
        r.raise_for_status()

        total = int(r.headers.get("Content-Length", "0")) or None
        downloaded = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = 100 * downloaded / total
                        print(f"\rDownloading... {pct:5.1f}% ({downloaded}/{total} bytes)", end="")
        print("\nDone:", out_path)

def main():
    p = argparse.ArgumentParser(description="Download a Panopto session MP4 using the API")
    p.add_argument("--server", required=True, help="e.g. myuni.hosted.panopto.com")
    p.add_argument("--client-id", required=True)
    p.add_argument("--client-secret", required=True)
    p.add_argument("--username", required=True, help="Panopto username (depends on your IdP setup)")
    p.add_argument("--password", required=True)
    p.add_argument("--session-id", required=True, help="Panopto Session GUID")
    p.add_argument("--output", required=True, help="Output file path, e.g. lecture.mp4")
    p.add_argument("--insecure", action="store_true", help="Skip SSL verification (not recommended)")
    args = p.parse_args()

    verify_ssl = not args.insecure

    # 1) Get an OAuth2 access token for this user (password grant).
    access_token = get_oauth_token_password_grant(
        server=args.server,
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
        verify_ssl=verify_ssl
    )

    # 2) Turn Bearer token into a legacy auth cookie.
    s = requests.Session()
    s.verify = verify_ssl
    legacy_login_with_cookie(args.server, access_token, s, verify_ssl=verify_ssl)

    # 3) Download the MP4 podcast for the session.
    download_podcast_mp4(args.server, args.session_id, args.output, s, verify_ssl=verify_ssl)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
