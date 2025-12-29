#!/usr/bin/env python3
"""
X (Twitter) に投稿するスクリプト
使い方: python scripts/post_to_x.py "投稿したいテキスト" [画像パス]
"""

import os
import sys
import json
import time
import random
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import ssl
import mimetypes

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがない場合は環境変数のみ使用

# 環境変数から認証情報を取得
API_KEY = os.environ.get('X_API_KEY')
API_SECRET = os.environ.get('X_API_SECRET')
ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET')

def get_ssl_context():
    """SSL証明書検証をスキップするコンテキストを取得"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def create_oauth_signature(method, url, params, api_secret, token_secret):
    """OAuth 1.0a 署名を生成"""
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    signature_base = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
    signing_key = f"{api_secret}&{token_secret}"
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode(),
            signature_base.encode(),
            hashlib.sha1
        ).digest()
    ).decode()
    return urllib.parse.quote(signature, safe='')

def upload_media(image_path):
    """画像をアップロードしてmedia_idを取得"""
    url = "https://upload.twitter.com/1.1/media/upload.json"

    # 画像を読み込んでBase64エンコード
    with open(image_path, 'rb') as f:
        media_data = base64.b64encode(f.read()).decode()

    # OAuthパラメータ
    oauth_params = {
        'oauth_consumer_key': API_KEY,
        'oauth_nonce': str(random.randint(0, 1000000000)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': ACCESS_TOKEN,
        'oauth_version': '1.0'
    }

    # 署名用にすべてのパラメータを含める
    all_params = oauth_params.copy()
    all_params['media_data'] = urllib.parse.quote(media_data, safe='')

    oauth_params['oauth_signature'] = create_oauth_signature(
        'POST', url, all_params, API_SECRET, ACCESS_TOKEN_SECRET
    )

    auth_header = 'OAuth ' + ', '.join([f'{k}="{v}"' for k, v in sorted(oauth_params.items())])

    # POSTデータ
    post_data = urllib.parse.urlencode({'media_data': media_data}).encode('utf-8')

    req = urllib.request.Request(url, data=post_data, headers={
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'v2TweetPython'
    })

    try:
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            result = json.loads(response.read().decode())
            media_id = result['media_id_string']
            print(f"✅ 画像をアップロードしました: {image_path}")
            print(f"   media_id: {media_id}")
            return media_id
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 画像アップロードエラー: {e.code} - {e.reason}")
        print(f"   詳細: {error_body}")
        return None

def post_tweet(text, media_ids=None):
    """ツイート投稿"""
    url = "https://api.twitter.com/2/tweets"

    oauth_params = {
        'oauth_consumer_key': API_KEY,
        'oauth_nonce': str(random.randint(0, 1000000000)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': ACCESS_TOKEN,
        'oauth_version': '1.0'
    }

    oauth_params['oauth_signature'] = create_oauth_signature(
        'POST', url, oauth_params, API_SECRET, ACCESS_TOKEN_SECRET
    )

    auth_header = 'OAuth ' + ', '.join([f'{k}="{v}"' for k, v in sorted(oauth_params.items())])

    tweet_data = {'text': text}
    if media_ids:
        tweet_data['media'] = {'media_ids': media_ids}
    body = json.dumps(tweet_data).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers={
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'User-Agent': 'v2TweetPython'
    })

    try:
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            result = json.loads(response.read().decode())
            print(f"✅ ツイートを投稿しました: {text}")
            print(f"   ツイートID: {result['data']['id']}")
            print(f"   URL: https://twitter.com/i/web/status/{result['data']['id']}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ ツイート投稿エラー: {e.code} - {e.reason}")
        print(f"   詳細: {error_body}")
        return False

if __name__ == "__main__":
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("❌ 環境変数を設定してください:")
        print("   export X_API_KEY='your_api_key'")
        print("   export X_API_SECRET='your_api_secret'")
        print("   export X_ACCESS_TOKEN='your_access_token'")
        print("   export X_ACCESS_TOKEN_SECRET='your_access_token_secret'")
        sys.exit(1)

    text = sys.argv[1] if len(sys.argv) > 1 else "おはよう"
    image_path = sys.argv[2] if len(sys.argv) > 2 else None

    media_ids = None
    if image_path:
        if os.path.exists(image_path):
            media_id = upload_media(image_path)
            if media_id:
                media_ids = [media_id]
            else:
                print("❌ 画像のアップロードに失敗したため、テキストのみで投稿します")
        else:
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            sys.exit(1)

    success = post_tweet(text, media_ids)
    sys.exit(0 if success else 1)
