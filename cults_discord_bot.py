import os
import sys
import json
import base64
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# Path to .env and state
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
ENV_PATH = os.path.join(DOCS_DIR, ".env")
LOCAL_ENV_PATH = os.path.join(BASE_DIR, ".env")
STATE_PATH = os.path.join(BASE_DIR, "cults_bot_state.json")

def load_env():
    env = {}
    for p in (ENV_PATH, LOCAL_ENV_PATH):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            env[k.strip()] = v.strip()
            except Exception:
                pass
    return env

FILE_ENV = load_env()

# Read from OS environment first (for GitHub Actions secrets), fallback to .env file
API_KEY = os.environ.get("CULTS_API_KEY") or FILE_ENV.get("CULTS_API_KEY", "")
USERNAME = os.environ.get("CULTS_USERNAME") or FILE_ENV.get("CULTS_USERNAME", "EasyDesigns")
WEBHOOK_SALE = os.environ.get("DISCORD_WEBHOOK_SALE") or FILE_ENV.get("DISCORD_WEBHOOK_SALE", "")
WEBHOOK_REPORT = os.environ.get("DISCORD_WEBHOOK_REPORT") or FILE_ENV.get("DISCORD_WEBHOOK_REPORT", "")
WEBHOOK_MESSAGE = os.environ.get("DISCORD_WEBHOOK_MESSAGE") or FILE_ENV.get("DISCORD_WEBHOOK_MESSAGE", "")

def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"known_sales": [], "known_comments": [], "last_views": 0, "last_downloads": 0}

def save_state(state):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Warning: could not save state:", e)

def country_flag(code):
    if not code or len(code) != 2:
        return ""
    code = code.upper()
    try:
        return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)
    except Exception:
        return ""

def query_cults(query):
    auth_str = f"{USERNAME}:{API_KEY}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    req = urllib.request.Request(
        "https://cults3d.com/graphql",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def send_discord_webhook(webhook_url, payload):
    if not webhook_url:
        print("Webhook URL missing!")
        return False
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print("Failed to send webhook:", e)
        return False

def check_sales(force_notify=False):
    print("Checking for Cults3D sales...")
    state = load_state()
    known_sales = set(state.get("known_sales", []))

    query = """
    {
      myself {
        salesBatch(limit: 10) {
          total
          results {
            id
            createdAt
            orderCountry {
              name
              code
            }
            income {
              cents
              currency
            }
            buyer {
              nick
            }
            creation {
              name
              url
              illustrationImageUrl
              viewsCount
              downloadsCount
            }
          }
        }
      }
    }
    """
    res = query_cults(query)
    data = res.get("data", {}).get("myself", {})
    sales = data.get("salesBatch", {}).get("results", [])

    new_sales_count = 0
    for s in sales:
        sale_id = s.get("id")
        if force_notify or (sale_id not in known_sales):
            c = s.get("creation", {})
            b = s.get("buyer", {})
            country = s.get("orderCountry", {})
            income = s.get("income", {})

            cents = income.get("cents", 0)
            currency = income.get("currency", "EUR")
            amount_str = f"€{cents / 100:.2f} {currency}"

            c_name = c.get("name", "DIY 3D Design")
            c_url = c.get("url", "https://cults3d.com")
            thumb = c.get("illustrationImageUrl", "")
            buyer_nick = b.get("nick", "Anonymous Maker")
            country_name = country.get("name", "Unknown")
            flag = country_flag(country.get("code", ""))

            # Format timestamp
            created_at = s.get("createdAt", "")
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                dt_str = dt.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
            except Exception:
                dt_str = created_at

            embed = {
                "title": "🎉 [NEW SALE] 새로운 주문이 접수되었습니다!",
                "description": f"**[{c_name}]({c_url})**\nCults3D에서 새로운 해외 주문이 성사되었습니다.",
                "color": 0x10B981, # Emerald Green
                "fields": [
                    {"name": "👤 구매 고객", "value": f"`{buyer_nick}`", "inline": True},
                    {"name": "🌍 구매 국가", "value": f"{flag} {country_name}", "inline": True},
                    {"name": "💰 정산 수익", "value": f"**{amount_str}** (순수익)", "inline": True},
                    {"name": "📦 제품 바로가기", "value": f"[Cults3D 제품 페이지 열기 ↗]({c_url})", "inline": False},
                    {"name": "⏱️ 주문 일시", "value": f"{dt_str}", "inline": False}
                ],
                "footer": {"text": "Cults3D EasyDesigns Sale Tracker • Real-time Notification"}
            }
            if thumb:
                embed["thumbnail"] = {"url": thumb}

            payload = {
                "username": "Cults3D EasyDesigns Sale Alert",
                "avatar_url": "https://cults3d.com/favicon.png",
                "content": "@everyone 🎉 **[NEW SALE]** 새로운 Cults3D 주문이 접수되었습니다!",
                "embeds": [embed]
            }

            print(f"Sending sale alert for {sale_id} by {buyer_nick}...")
            if send_discord_webhook(WEBHOOK_SALE, payload):
                print(f"Sale alert sent successfully for {sale_id}!")
                known_sales.add(sale_id)
                new_sales_count += 1
            else:
                print(f"Failed sending alert for {sale_id}")

    state["known_sales"] = list(known_sales)
    save_state(state)
    print(f"Check sales complete. {new_sales_count} new sale(s) processed.")

def check_comments(force_notify=False):
    print("Checking for Cults3D comments & customer messages...")
    state = load_state()
    known_comments = set(state.get("known_comments", []))

    query = """
    {
      myself {
        commentsBatch(limit: 10) {
          total
          results {
            text
            publishedAt
            creator {
              nick
              url
            }
            commented {
              __typename
              ... on Creation {
                name
                url
              }
            }
          }
        }
      }
    }
    """
    res = query_cults(query)
    data = res.get("data", {}).get("myself", {})
    comments = data.get("commentsBatch", {}).get("results", [])

    new_comments_count = 0
    target_webhook = WEBHOOK_MESSAGE or WEBHOOK_SALE

    for cm in comments:
        c_creator = cm.get("creator", {})
        creator_nick = c_creator.get("nick", "User")
        published_at = cm.get("publishedAt", "")
        text = cm.get("text", "").strip()

        # Generate unique hash for this comment
        c_hash = hashlib.md5(f"{creator_nick}_{published_at}_{text[:40]}".encode("utf-8")).hexdigest()

        # Skip our own replies to avoid self-notification
        if creator_nick.lower() == USERNAME.lower() and not force_notify:
            known_comments.add(c_hash)
            continue

        if force_notify or (c_hash not in known_comments):
            commented_obj = cm.get("commented", {})
            target_name = commented_obj.get("name", "EasyDesigns Profile / 3D Model")
            target_url = commented_obj.get("url", f"https://cults3d.com/en/users/{USERNAME}/comments")
            reply_url = f"https://cults3d.com/en/users/{USERNAME}/comments"

            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                dt_str = dt.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
            except Exception:
                dt_str = published_at

            # Truncate text if very long for embed description
            display_text = text if len(text) <= 1000 else text[:997] + "..."

            embed = {
                "title": "💬 [NEW COMMENT] 새로운 고객 문의/댓글이 등록되었습니다!",
                "description": f"**\"{display_text}\"**",
                "color": 0xA855F7, # Purple / Violet
                "fields": [
                    {"name": "👤 작성자", "value": f"`@{creator_nick}`", "inline": True},
                    {"name": "📦 대상", "value": f"[{target_name[:35]}]({target_url})", "inline": True},
                    {"name": "⏱️ 등록 일시", "value": f"{dt_str}", "inline": True},
                    {"name": "💬 답변하기", "value": f"[Cults3D에서 답글 작성하기 ↗]({reply_url})", "inline": False}
                ],
                "footer": {"text": "Cults3D EasyDesigns Customer Q&A Tracker"}
            }

            payload = {
                "username": "Cults3D EasyDesigns Q&A Bot",
                "avatar_url": "https://cults3d.com/favicon.png",
                "content": "@everyone 💬 **[NEW COMMENT]** 새로운 고객 문의/댓글이 도착했습니다!",
                "embeds": [embed]
            }

            print(f"Sending comment alert from @{creator_nick}...")
            if send_discord_webhook(target_webhook, payload):
                print(f"Comment alert sent successfully!")
                known_comments.add(c_hash)
                new_comments_count += 1
            else:
                print(f"Failed sending comment alert")

    state["known_comments"] = list(known_comments)
    save_state(state)
    print(f"Check comments complete. {new_comments_count} new comment(s) processed.")

def send_daily_report():
    print("Generating Daily Summary Report...")
    query = """
    {
      myself {
        user {
          nick
          followersCount
          creationsCount
        }
        commentsBatch(limit: 1) {
          total
        }
        salesBatch(limit: 50) {
          total
          results {
            income {
              cents
              currency
            }
          }
        }
        creationsBatch(limit: 20) {
          total
          results {
            name
            url
            viewsCount
            downloadsCount
            likesCount
            price {
              cents
              currency
            }
          }
        }
      }
    }
    """
    res = query_cults(query)
    data = res.get("data", {}).get("myself", {})
    user = data.get("user", {})
    creations = data.get("creationsBatch", {}).get("results", [])
    sales_total = data.get("salesBatch", {}).get("total", 0)
    sales = data.get("salesBatch", {}).get("results", [])
    total_comments = data.get("commentsBatch", {}).get("total", 0)

    total_income_cents = sum(s.get("income", {}).get("cents", 0) for s in sales)
    total_views = sum(c.get("viewsCount", 0) for c in creations)
    total_downloads = sum(c.get("downloadsCount", 0) for c in creations)
    total_likes = sum(c.get("likesCount", 0) for c in creations)

    today_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    # Creation details
    models_summary = []
    for c in creations:
        name = c.get("name", "")
        url = c.get("url", "")
        v = c.get("viewsCount", 0)
        d = c.get("downloadsCount", 0)
        l = c.get("likesCount", 0)
        price_cents = c.get("price", {}).get("cents", 0)
        models_summary.append(
            f"• **[{name[:42]}...]({url})**\n  └ 👁️ {v}회 | 📥 {d}회 | ❤️ {l}개 | 가격: €{price_cents/100:.2f}"
        )

    models_text = "\n".join(models_summary) if models_summary else "등록된 모델 없음"

    embed = {
        "title": "📊 [DAILY REPORT] EasyDesigns Cults3D 성과 브리핑",
        "description": f"**EasyDesigns** 브랜드의 3D 설계 키트 누적 마켓플레이스 실적 리포트입니다.\n*(집계 시각: {today_str})*",
        "color": 0x3B82F6, # Royal Blue
        "fields": [
            {"name": "👀 총 조회수", "value": f"**{total_views}** 회", "inline": True},
            {"name": "📥 총 다운로드", "value": f"**{total_downloads}** 회", "inline": True},
            {"name": "❤️ 누적 좋아요", "value": f"**{total_likes}** 개", "inline": True},
            {"name": "👥 팔로워", "value": f"**{user.get('followersCount', 0)}** 명", "inline": True},
            {"name": "🛒 총 판매 건수", "value": f"**{sales_total}** 건", "inline": True},
            {"name": "💶 총 누적 순익", "value": f"**€{total_income_cents/100:.2f} EUR**", "inline": True},
            {"name": "💬 누적 댓글/문의", "value": f"**{total_comments}** 건", "inline": True},
            {"name": "🛠️ 등록된 3D 제품별 현황", "value": models_text, "inline": False}
        ],
        "footer": {"text": "Cults3D EasyDesigns Analytics • Daily Automated Briefing"}
    }

    payload = {
        "username": "Cults3D EasyDesigns Daily Digest",
        "avatar_url": "https://cults3d.com/favicon.png",
        "content": "@everyone 📊 **[DAILY REPORT]** 오늘의 EasyDesigns Cults3D 성과 브리핑이 도착했습니다!",
        "embeds": [embed]
    }

    print("Sending daily report webhook...")
    if send_discord_webhook(WEBHOOK_REPORT, payload):
        print("Daily report sent successfully!")
    else:
        print("Failed to send daily report.")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if mode == "--test-sale":
        check_sales(force_notify=True)
    elif mode == "--test-comment":
        check_comments(force_notify=True)
    elif mode == "--check-sales":
        check_sales(force_notify=False)
    elif mode == "--check-comments":
        check_comments(force_notify=False)
    elif mode == "--daily-report":
        send_daily_report()
    elif mode == "--all":
        check_sales(force_notify=False)
        check_comments(force_notify=True)
        send_daily_report()
    else:
        print("Unknown mode. Use: --test-sale | --test-comment | --check-sales | --check-comments | --daily-report | --all")
