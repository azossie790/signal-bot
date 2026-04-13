"""
╔══════════════════════════════════════════════════════════════╗
║         SIGNAL BOT V6 — ULTIMATE SNIPER EDITION             ║
║  Price Action | SMC CHoCH/BOS | DXY | Niveaux Clés          ║
║  Optimisé 800 req/jour | Multi-TP | Railway                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, time, json, random, asyncio, logging, requests
import pandas as pd
import numpy as np
import schedule
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from telegram import Bot
from telegram.constants import ParseMode

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8633331614:AAHKOhSFUvRXUiWjM32ZPX8L9_2mBx7ePAA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@signaltraidingv2")
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY",   "2773a81a7d494b66a12b4dee358e81cb")

SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "GBP/JPY", "EUR/JPY",
    "XAU/USD", "XAG/USD",
    "BTC/USD", "ETH/USD",
]

CRYPTO = {"BTC/USD", "ETH/USD"}

MIN_SCORE   = 60
MAX_ACTIFS  = 3
MIN_ADX     = 18
MIN_RR      = 1.5

SIGNALS_FILE = "signals.json"
HISTORY_FILE = "history.json"
LEVELS_FILE  = "key_levels.json"

# Compteur de scan pour alterner timeframes
scan_counter = {"n": 0}

# Cache DXY et niveaux clés (rechargé 1x/jour)
cache = {
    "dxy":          None,
    "key_levels":   {},
    "last_refresh": None,
}

# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_v6.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
#  CONTENU CANAL
# ══════════════════════════════════════════════════════════════

CITATIONS = [
    "💬 _\"Coupez vos pertes rapidement, laissez courir vos profits.\"_\n— Jesse Livermore",
    "💬 _\"Le marché peut rester irrationnel plus longtemps que vous ne pouvez rester solvable.\"_\n— Keynes",
    "💬 _\"La discipline est la différence entre un bon trader et un mauvais trader.\"_\n— Mark Douglas",
    "💬 _\"Ne risquez jamais ce que vous ne pouvez pas vous permettre de perdre.\"_\n— Warren Buffett",
    "💬 _\"Un bon trader sait quand ne pas trader.\"_\n— Jesse Livermore",
    "💬 _\"Gérez votre risque avant de penser aux profits.\"_\n— Paul Tudor Jones",
    "💬 _\"La patience est la vertu la plus rentable en trading.\"_\n— Nicolas Darvas",
    "💬 _\"Le trading est simple, mais pas facile.\"_\n— Ed Seykota",
    "💬 _\"Les marchés sont guidés par la peur et la cupidité.\"_\n— Warren Buffett",
    "💬 _\"Votre plan de trading est votre meilleur ami.\"_\n— Alexander Elder",
    "💬 _\"Chaque perte est une leçon. Chaque gain est une confirmation.\"_\n— Anonyme",
    "💬 _\"Le meilleur trade est parfois celui qu'on ne prend pas.\"_\n— Paul Tudor Jones",
]

HUMOUR = [
    "😂 *Moi avant le trade :* \"Je vais juste regarder...\"\n*Moi 3h après :* 📉💸😭",
    "🤡 *Le marché quand j'achète :* descend\n*Le marché quand je vends :* monte\n\nLogique ? 😭",
    "😅 *SL touché à -15 pips*\nLe marché 5 min après : 📈+200 pips\n_\"Bien sûr...\"_ 😑",
    "🧘 *Méditation du trader :*\nFerme les yeux → Respire → Ne regarde PAS le graphique → Répète 😂",
    "💀 *Mon portefeuille après avoir ignoré le SL :*\n📉📉📉\n*Leçon : TOUJOURS mettre le SL* ✅",
    "🤓 *J'ai analysé 6h, 12 indicateurs, 5 timeframes...*\nLe marché : fait exactement l'inverse 😭",
    "💪 *Un trader perdant est juste un trader gagnant qui n'a pas encore arrêté.* 🔥",
    "🎰 *Différence trading/casino ?*\nAu casino on te donne des boissons gratuites 😂",
    "😤 *Quand le signal dit BUY et que ta femme dit NON :*\nDans les deux cas tu perds de l'argent 😅",
]

MOTIVATION = [
    "🔥 *La patience est la clé.* Pas de signal = pas de perte !",
    "💪 *Ne forcez jamais un trade.* Le marché sera là demain.",
    "🧠 *Les pros ne cherchent pas à tout trader — ils cherchent LES bons trades.*",
    "⚡ *Discipline > Émotion.* Suivez le plan.",
    "🎯 *3 bons signaux valent mieux que 20 mauvais.*",
    "🛡️ *Protégez votre capital d'abord.* Les profits viennent ensuite.",
    "📈 *Le trend est votre ami.* Ne tradez jamais contre la tendance principale.",
]

MATIN = [
    "🌅 *BONJOUR TRADERS !*\n\nNouvelle session, nouvelles opportunités !\n📊 Bot actif — analyse en continu.\n💪 Bonne session !",
    "☀️ *RÉVEIL DU TRADER !*\n\nSession de Londres bientôt !\nMeilleurs setups souvent là.\n🎯 On reste focus ! Let's go !",
    "🔔 *SESSION EUROPÉENNE BIENTÔT !*\n\nTop paires surveillées :\n→ XAU/USD 👀\n→ EUR/USD 👀\n→ GBP/USD 👀\n🤖 Bot en veille",
]

SOIR = [
    "🌙 *FIN DE SESSION !*\n\nSession américaine termine.\n💤 Bot continue de surveiller.\nBonne nuit traders ! 😴",
    "🌆 *BILAN DE SOIRÉE*\n\nConsultez le résumé ci-dessous.\n🙏 Merci d'être avec nous !\nOn se retrouve demain 💪",
]

# ══════════════════════════════════════════════════════════════
#  TWELVE DATA — FETCH
# ══════════════════════════════════════════════════════════════

BASE = "https://api.twelvedata.com"

def fetch_ohlcv(symbol: str, interval: str, bars: int = 150) -> Optional[pd.DataFrame]:
    try:
        r = requests.get(f"{BASE}/time_series", params={
            "symbol": symbol, "interval": interval,
            "outputsize": bars, "apikey": TWELVEDATA_KEY
        }, timeout=15)
        d = r.json()
        if d.get("status") == "error":
            log.warning(f"{symbol} {interval}: {d.get('message')}")
            return None
        vals = d.get("values", [])
        if not vals: return None
        df = pd.DataFrame(vals)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        for c in ["open","high","low","close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df.dropna(inplace=True)
        return df.sort_index()
    except Exception as e:
        log.error(f"fetch {symbol} {interval}: {e}")
        return None

def fetch_price(symbol: str) -> Optional[float]:
    try:
        r = requests.get(f"{BASE}/price", params={
            "symbol": symbol, "apikey": TWELVEDATA_KEY
        }, timeout=10)
        v = float(r.json().get("price", 0) or 0)
        return v if v > 0 else None
    except:
        return None

def get_digits(symbol: str) -> int:
    s = symbol.replace("/","")
    if "JPY" in s: return 3
    if "BTC" in s: return 2
    if "ETH" in s: return 2
    if "XAU" in s: return 2
    if "XAG" in s: return 3
    return 5

# ══════════════════════════════════════════════════════════════
#  CACHE DXY + NIVEAUX CLÉS (1x/jour)
# ══════════════════════════════════════════════════════════════

def refresh_daily_cache():
    """Rafraîchit DXY et niveaux clés une fois par jour."""
    log.info("🔄 Rafraîchissement cache DXY + niveaux clés...")

    # DXY — Indice Dollar
    try:
        df_dxy = fetch_ohlcv("DX/Y", "1day", 50)
        time.sleep(1)
        if df_dxy is not None:
            dxy_close = float(df_dxy["close"].iloc[-1])
            dxy_prev  = float(df_dxy["close"].iloc[-2])
            dxy_trend = "HAUSSIER" if dxy_close > dxy_prev else "BAISSIER"
            dxy_ma20  = float(df_dxy["close"].ewm(span=20).mean().iloc[-1])
            cache["dxy"] = {
                "price":  dxy_close,
                "trend":  dxy_trend,
                "ma20":   dxy_ma20,
                "strong": dxy_close > dxy_ma20,
            }
            log.info(f"DXY: {dxy_close:.2f} | Trend: {dxy_trend}")
    except Exception as e:
        log.warning(f"DXY fetch error: {e}")
        cache["dxy"] = None

    # Niveaux clés hebdo + mensuel pour chaque symbole
    for symbol in SYMBOLS[:6]:  # On prend les 6 premières pour économiser les requêtes
        try:
            df_w = fetch_ohlcv(symbol, "1week", 10)
            time.sleep(0.8)
            df_m = fetch_ohlcv(symbol, "1month", 6)
            time.sleep(0.8)

            levels = {}
            if df_w is not None:
                levels["weekly_high"] = float(df_w["high"].iloc[-2])
                levels["weekly_low"]  = float(df_w["low"].iloc[-2])
                levels["weekly_open"] = float(df_w["open"].iloc[-1])

            if df_m is not None:
                levels["monthly_high"] = float(df_m["high"].iloc[-2])
                levels["monthly_low"]  = float(df_m["low"].iloc[-2])
                levels["monthly_open"] = float(df_m["open"].iloc[-1])

            clean = symbol.replace("/","")
            cache["key_levels"][clean] = levels
            log.info(f"Niveaux clés {clean}: W_H={levels.get('weekly_high','?')}")
        except Exception as e:
            log.warning(f"Key levels {symbol}: {e}")

    cache["last_refresh"] = datetime.now(timezone.utc).date()
    log.info("✅ Cache DXY + niveaux clés rafraîchi")

def get_dxy_bias(direction: str) -> Tuple[bool, str]:
    """
    Corrélation DXY :
    DXY fort → USD monte → paires USD/XXX haussières, XXX/USD baissières
    DXY faible → USD baisse → paires USD/XXX baissières, XXX/USD haussières
    XAU/USD → inverse DXY (or monte quand dollar baisse)
    """
    dxy = cache.get("dxy")
    if not dxy:
        return True, ""  # Pas de data → on ne bloque pas

    dxy_strong = dxy["strong"]
    note = f"DXY {'fort 💪' if dxy_strong else 'faible 😮‍💨'} ({dxy['price']:.2f})"
    return True, note  # On informe sans bloquer

# ══════════════════════════════════════════════════════════════
#  INDICATEURS TECHNIQUES
# ══════════════════════════════════════════════════════════════

def calc_rsi(s: pd.Series, p=14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(span=p, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(span=p, adjust=False).mean()
    return 100 - 100/(1 + g/l.replace(0, np.nan))

def calc_macd(s: pd.Series):
    m = s.ewm(span=12,adjust=False).mean() - s.ewm(span=26,adjust=False).mean()
    return m, m.ewm(span=9,adjust=False).mean()

def calc_atr(df: pd.DataFrame, p=14) -> pd.Series:
    h,l,c = df["high"],df["low"],df["close"]
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(span=p,adjust=False).mean()

def calc_bb(s: pd.Series, p=20, k=2.0):
    mid = s.rolling(p).mean()
    std = s.rolling(p).std()
    return mid+k*std, mid, mid-k*std

def calc_stoch(df: pd.DataFrame, k=14, d=3):
    lo = df["low"].rolling(k).min()
    hi = df["high"].rolling(k).max()
    pk = 100*(df["close"]-lo)/(hi-lo+1e-10)
    return pk, pk.rolling(d).mean()

def calc_adx(df: pd.DataFrame, p=14):
    h,l = df["high"],df["low"]
    up,dn = h.diff(),-l.diff()
    pdm = up.where((up>dn)&(up>0),0.0)
    ndm = dn.where((dn>up)&(dn>0),0.0)
    av = calc_atr(df,p)
    pdi = 100*pdm.ewm(span=p,adjust=False).mean()/av.replace(0,np.nan)
    ndi = 100*ndm.ewm(span=p,adjust=False).mean()/av.replace(0,np.nan)
    dx  = 100*(pdi-ndi).abs()/(pdi+ndi).replace(0,np.nan)
    return dx.ewm(span=p,adjust=False).mean(), pdi, ndi

def calc_stochrsi(s: pd.Series, p=14) -> pd.Series:
    rsi = calc_rsi(s, p)
    lo, hi = rsi.rolling(p).min(), rsi.rolling(p).max()
    return 100*(rsi-lo)/(hi-lo+1e-10)

def calc_wr(df: pd.DataFrame, p=14) -> pd.Series:
    hi = df["high"].rolling(p).max()
    lo = df["low"].rolling(p).min()
    return -100*(hi-df["close"])/(hi-lo+1e-10)

# ══════════════════════════════════════════════════════════════
#  PRICE ACTION — PATTERNS DE BOUGIES
# ══════════════════════════════════════════════════════════════

def detect_candle_patterns(df: pd.DataFrame) -> dict:
    """Détecte les patterns de bougies les plus fiables."""
    try:
        c = df.tail(4).copy()
        c["body"]       = (c["close"] - c["open"]).abs()
        c["upper_wick"] = c["high"] - c[["close","open"]].max(axis=1)
        c["lower_wick"] = c[["close","open"]].min(axis=1) - c["low"]
        c["range"]      = c["high"] - c["low"]

        last  = c.iloc[-1]
        prev  = c.iloc[-2]
        prev2 = c.iloc[-3]

        patterns = {
            "bullish_engulfing": False,
            "bearish_engulfing": False,
            "hammer":           False,
            "shooting_star":    False,
            "pin_bar_bull":     False,
            "pin_bar_bear":     False,
            "inside_bar":       False,
            "doji":             False,
            "morning_star":     False,
            "evening_star":     False,
        }

        # Engulfing haussier
        if (prev["close"] < prev["open"] and
            last["close"] > last["open"] and
            last["close"] > prev["open"] and
            last["open"]  < prev["close"]):
            patterns["bullish_engulfing"] = True

        # Engulfing baissier
        if (prev["close"] > prev["open"] and
            last["close"] < last["open"] and
            last["close"] < prev["open"] and
            last["open"]  > prev["close"]):
            patterns["bearish_engulfing"] = True

        # Hammer (marteau) — bougie haussière
        if (last["lower_wick"] > last["body"] * 2 and
            last["upper_wick"] < last["body"] * 0.5 and
            last["close"] > last["open"]):
            patterns["hammer"] = True

        # Shooting Star — bougie baissière
        if (last["upper_wick"] > last["body"] * 2 and
            last["lower_wick"] < last["body"] * 0.5 and
            last["close"] < last["open"]):
            patterns["shooting_star"] = True

        # Pin Bar haussier — longue mèche basse
        if (last["lower_wick"] > last["range"] * 0.6 and
            last["body"] < last["range"] * 0.3):
            patterns["pin_bar_bull"] = True

        # Pin Bar baissier — longue mèche haute
        if (last["upper_wick"] > last["range"] * 0.6 and
            last["body"] < last["range"] * 0.3):
            patterns["pin_bar_bear"] = True

        # Inside Bar — bougie contenue dans la précédente
        if (last["high"] < prev["high"] and last["low"] > prev["low"]):
            patterns["inside_bar"] = True

        # Doji — corps très petit
        if last["body"] < last["range"] * 0.1:
            patterns["doji"] = True

        # Morning Star (3 bougies) — signal haussier
        if (prev2["close"] < prev2["open"] and
            prev["body"]   < prev2["body"] * 0.5 and
            last["close"]  > last["open"] and
            last["close"]  > (prev2["open"] + prev2["close"]) / 2):
            patterns["morning_star"] = True

        # Evening Star (3 bougies) — signal baissier
        if (prev2["close"] > prev2["open"] and
            prev["body"]   < prev2["body"] * 0.5 and
            last["close"]  < last["open"] and
            last["close"]  < (prev2["open"] + prev2["close"]) / 2):
            patterns["evening_star"] = True

        return patterns
    except:
        return {}

def pa_score(patterns: dict, direction: str) -> Tuple[int, list]:
    """Score Price Action selon la direction."""
    score = 0
    found = []
    buy = direction == "BUY"

    bullish = ["bullish_engulfing", "hammer", "pin_bar_bull", "morning_star"]
    bearish = ["bearish_engulfing", "shooting_star", "pin_bar_bear", "evening_star"]

    weights = {
        "bullish_engulfing": 12, "bearish_engulfing": 12,
        "morning_star":      10, "evening_star":      10,
        "hammer":             8, "shooting_star":      8,
        "pin_bar_bull":       8, "pin_bar_bear":       8,
        "inside_bar":         4, "doji":               3,
    }

    relevant = bullish if buy else bearish
    for p in relevant:
        if patterns.get(p):
            score += weights.get(p, 5)
            name = p.replace("_"," ").title()
            found.append(f"🕯️ {name}")

    # Pénalité si pattern opposé
    opposite = bearish if buy else bullish
    for p in opposite:
        if patterns.get(p):
            score -= 5

    return max(score, 0), found

# ══════════════════════════════════════════════════════════════
#  SMC AVANCÉ — CHoCH, BOS, MSB
# ══════════════════════════════════════════════════════════════

def detect_choch_bos(df: pd.DataFrame) -> dict:
    """
    CHoCH = Change of Character — premier signe de retournement
    BOS   = Break of Structure — confirmation du retournement
    MSB   = Market Structure Break — rupture majeure
    """
    try:
        c = df["close"].tail(30).values
        h = df["high"].tail(30).values
        l = df["low"].tail(30).values

        # Trouver les swing highs et lows
        swing_highs = []
        swing_lows  = []
        for i in range(2, len(c)-2):
            if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
                swing_highs.append((i, h[i]))
            if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
                swing_lows.append((i, l[i]))

        result = {
            "choch_bull": False,
            "choch_bear": False,
            "bos_bull":   False,
            "bos_bear":   False,
            "msb_bull":   False,
            "msb_bear":   False,
        }

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_sh  = swing_highs[-1][1]
            prev_sh  = swing_highs[-2][1]
            last_sl  = swing_lows[-1][1]
            prev_sl  = swing_lows[-2][1]
            current  = c[-1]

            # BOS haussier — prix casse au-dessus du dernier swing high
            if current > last_sh and last_sh > prev_sh:
                result["bos_bull"] = True

            # BOS baissier — prix casse en-dessous du dernier swing low
            if current < last_sl and last_sl < prev_sl:
                result["bos_bear"] = True

            # CHoCH haussier — après tendance baissière, prix casse un swing high
            if last_sh < prev_sh and current > last_sh:
                result["choch_bull"] = True

            # CHoCH baissier — après tendance haussière, prix casse un swing low
            if last_sl > prev_sl and current < last_sl:
                result["choch_bear"] = True

            # MSB — rupture majeure (2 niveaux consécutifs cassés)
            if result["bos_bull"] and result["choch_bull"]:
                result["msb_bull"] = True
            if result["bos_bear"] and result["choch_bear"]:
                result["msb_bear"] = True

        return result
    except:
        return {}

def smc_score(choch_bos: dict, ob: Optional[dict], fvg: bool,
              liq: dict, direction: str) -> Tuple[int, list]:
    """Score SMC complet."""
    score = 0
    found = []
    buy = direction == "BUY"

    # CHoCH (15 pts)
    if (choch_bos.get("choch_bull") if buy else choch_bos.get("choch_bear")):
        score += 15
        found.append(f"🔄 CHoCH {'haussier' if buy else 'baissier'} détecté")

    # BOS (12 pts)
    if (choch_bos.get("bos_bull") if buy else choch_bos.get("bos_bear")):
        score += 12
        found.append(f"💥 BOS {'haussier' if buy else 'baissier'}")

    # MSB (bonus 8 pts si les deux)
    if (choch_bos.get("msb_bull") if buy else choch_bos.get("msb_bear")):
        score += 8
        found.append(f"🚀 MSB confirmé !")

    # Order Block (10 pts)
    if ob:
        score += 10
        found.append("🧱 Order Block institutionnel")

    # FVG (7 pts)
    if fvg:
        score += 7
        found.append("🌐 Fair Value Gap présent")

    # Liquidité (6 pts)
    if buy and liq.get("buy_liquidity"):
        score += 6
        found.append("💧 Zone liquidité BUY")
    elif not buy and liq.get("sell_liquidity"):
        score += 6
        found.append("💧 Zone liquidité SELL")

    return score, found

# ══════════════════════════════════════════════════════════════
#  NIVEAUX CLÉS
# ══════════════════════════════════════════════════════════════

def check_key_levels(symbol: str, price: float, direction: str) -> Tuple[int, list]:
    """Vérifie si le prix est proche d'un niveau clé hebdo/mensuel."""
    clean = symbol.replace("/","")
    levels = cache["key_levels"].get(clean, {})
    if not levels:
        return 0, []

    score = 0
    found = []
    tolerance = price * 0.002  # 0.2% de tolérance

    key_map = {
        "weekly_high":  ("Résistance hebdo", False),  # résistance → bon pour SELL
        "weekly_low":   ("Support hebdo",    True),   # support → bon pour BUY
        "monthly_high": ("Résistance mensuelle", False),
        "monthly_low":  ("Support mensuel",  True),
        "weekly_open":  ("Open hebdo",       None),
        "monthly_open": ("Open mensuel",     None),
    }

    for key, (label, is_support) in key_map.items():
        level = levels.get(key)
        if not level:
            continue
        if abs(price - level) <= tolerance:
            if is_support is None:
                score += 5
                found.append(f"📍 Près {label} ({level:.4f})")
            elif (is_support and direction == "BUY") or (not is_support and direction == "SELL"):
                score += 10
                found.append(f"🎯 Sur {label} ({level:.4f})")
            else:
                score -= 5  # Contre le niveau

    return score, found

# ══════════════════════════════════════════════════════════════
#  LIQUIDITÉ + SWEEP
# ══════════════════════════════════════════════════════════════

def detect_liquidity(df: pd.DataFrame, window=25) -> dict:
    try:
        r = df.tail(window)
        highs, lows = r["high"].values, r["low"].values
        eq_high = eq_low = None

        for i in range(len(highs)-1):
            for j in range(i+1, len(highs)):
                if abs(highs[i]-highs[j])/highs[i] < 0.001:
                    eq_high = max(highs[i], highs[j]); break

        for i in range(len(lows)-1):
            for j in range(i+1, len(lows)):
                if abs(lows[i]-lows[j])/lows[i] < 0.001:
                    eq_low = min(lows[i], lows[j]); break

        return {
            "buy_liquidity":  eq_low,
            "sell_liquidity": eq_high,
            "resistance":     float(r["high"].max()),
            "support":        float(r["low"].min()),
        }
    except:
        return {"buy_liquidity": None, "sell_liquidity": None,
                "resistance": 0, "support": 0}

def detect_sweep(df: pd.DataFrame, direction: str, liq: dict) -> bool:
    try:
        r = df.tail(6)
        if direction == "BUY":
            level = liq.get("buy_liquidity")
            if not level: return True
            for i in range(len(r)-2):
                if r["low"].iloc[i] < level and r["close"].iloc[i+1] > level:
                    return True
            return r["low"].iloc[-2] < level and r["close"].iloc[-1] > level
        else:
            level = liq.get("sell_liquidity")
            if not level: return True
            for i in range(len(r)-2):
                if r["high"].iloc[i] > level and r["close"].iloc[i+1] < level:
                    return True
            return r["high"].iloc[-2] > level and r["close"].iloc[-1] < level
    except:
        return True

def detect_order_block(df: pd.DataFrame, direction: str) -> Optional[dict]:
    try:
        r = df.tail(30).copy()
        r["body"] = r["close"] - r["open"]
        if direction == "BUY":
            for i in range(len(r)-3, 0, -1):
                if r["body"].iloc[i] < 0 and r["close"].iloc[i+1] > r["high"].iloc[i]:
                    return {"high": float(r["high"].iloc[i]),
                            "low":  float(r["low"].iloc[i])}
        else:
            for i in range(len(r)-3, 0, -1):
                if r["body"].iloc[i] > 0 and r["close"].iloc[i+1] < r["low"].iloc[i]:
                    return {"high": float(r["high"].iloc[i]),
                            "low":  float(r["low"].iloc[i])}
        return None
    except:
        return None

def detect_fvg(df: pd.DataFrame, direction: str) -> bool:
    try:
        c = df.tail(5)
        for i in range(2, len(c)):
            if direction == "BUY" and c["low"].iloc[i] > c["high"].iloc[i-2]:
                return True
            if direction == "SELL" and c["high"].iloc[i] < c["low"].iloc[i-2]:
                return True
        return False
    except:
        return False

def market_structure(df: pd.DataFrame) -> str:
    try:
        c = df["close"].tail(20).values
        highs, lows = [], []
        for i in range(1, len(c)-1):
            if c[i] > c[i-1] and c[i] > c[i+1]: highs.append(c[i])
            if c[i] < c[i-1] and c[i] < c[i+1]: lows.append(c[i])
        if len(highs) >= 2 and len(lows) >= 2:
            if highs[-1] > highs[-2] and lows[-1] > lows[-2]: return "BULLISH"
            if highs[-1] < highs[-2] and lows[-1] < lows[-2]: return "BEARISH"
        return "RANGING"
    except:
        return "RANGING"

def premium_discount(df: pd.DataFrame, price: float) -> str:
    try:
        hi = df["high"].tail(50).max()
        lo = df["low"].tail(50).min()
        pct = (price - lo) / (hi - lo) * 100 if (hi - lo) > 0 else 50
        if pct >= 75:   return f"PREMIUM ({pct:.0f}%)"
        elif pct <= 25: return f"DISCOUNT ({pct:.0f}%)"
        else:           return f"EQUILIBRE ({pct:.0f}%)"
    except:
        return "N/A"

# ══════════════════════════════════════════════════════════════
#  ANALYSE PAR TIMEFRAME
# ══════════════════════════════════════════════════════════════

def analyze_tf(df: pd.DataFrame) -> Optional[dict]:
    if len(df) < 50: return None
    try:
        c = df["close"]
        rv       = calc_rsi(c)
        mv, ms   = calc_macd(c)
        ema20    = c.ewm(span=20,adjust=False).mean()
        ema50    = c.ewm(span=50,adjust=False).mean()
        ema200   = c.ewm(span=200,adjust=False).mean()
        bb_u,_,bb_l = calc_bb(c)
        sk, sd   = calc_stoch(df)
        adx_v, pdi, ndi = calc_adx(df)
        srsi     = calc_stochrsi(c)
        wr       = calc_wr(df)
        return {
            "rsi":    float(rv.iloc[-1]),   "rsi_p":  float(rv.iloc[-2]),
            "macd":   float(mv.iloc[-1]),   "macd_s": float(ms.iloc[-1]),
            "macd_p": float(mv.iloc[-2]),   "ms_p":   float(ms.iloc[-2]),
            "ema20":  float(ema20.iloc[-1]),"ema50":  float(ema50.iloc[-1]),
            "ema200": float(ema200.iloc[-1]),
            "bb_u":   float(bb_u.iloc[-1]), "bb_l":   float(bb_l.iloc[-1]),
            "stoch_k":float(sk.iloc[-1]),   "stoch_d":float(sd.iloc[-1]),
            "adx":    float(adx_v.iloc[-1]),"pdi":    float(pdi.iloc[-1]),
            "ndi":    float(ndi.iloc[-1]),  "srsi":   float(srsi.iloc[-1]),
            "wr":     float(wr.iloc[-1]),   "close":  float(c.iloc[-1]),
            "atr":    float(calc_atr(df).iloc[-1]),
        }
    except Exception as e:
        log.error(f"analyze_tf: {e}")
        return None

# ══════════════════════════════════════════════════════════════
#  SCORE INDICATEURS CLASSIQUES
# ══════════════════════════════════════════════════════════════

def indicator_score(fast, med, slow, direction: str) -> Tuple[int, list]:
    score = 0
    found = []
    buy = direction == "BUY"

    # RSI (10 pts)
    if fast["rsi"] < 38 if buy else fast["rsi"] > 62:
        score += 5; found.append(f"📊 RSI M15 {'survendu' if buy else 'suracheté'} ({fast['rsi']:.0f})")
    if med["rsi"] < 52 if buy else med["rsi"] > 48:
        score += 5

    # StochRSI (8 pts)
    if fast["srsi"] < 25 if buy else fast["srsi"] > 75:
        score += 8; found.append(f"⚡ StochRSI ({fast['srsi']:.0f})")

    # Williams %R (6 pts)
    if fast["wr"] < -75 if buy else fast["wr"] > -25:
        score += 6; found.append(f"📉 W%R {fast['wr']:.1f}")

    # MACD (10 pts)
    cross = (fast["macd"]>fast["macd_s"] and fast["macd_p"]<=fast["ms_p"]) if buy \
       else (fast["macd"]<fast["macd_s"] and fast["macd_p"]>=fast["ms_p"])
    if cross:
        score += 6; found.append(f"🔀 MACD croise {'↑' if buy else '↓'}")
    if (med["macd"]>med["macd_s"]) if buy else (med["macd"]<med["macd_s"]):
        score += 4

    # EMA (10 pts)
    if (med["ema20"]>med["ema50"]) if buy else (med["ema20"]<med["ema50"]):
        score += 5; found.append(f"📈 EMA H1 {'haussière' if buy else 'baissière'}")
    if (slow["ema20"]>slow["ema200"]) if buy else (slow["ema20"]<slow["ema200"]):
        score += 5; found.append("📈 Tendance H4 confirmée")

    # Bollinger (6 pts)
    if (fast["close"]<fast["bb_l"]) if buy else (fast["close"]>fast["bb_u"]):
        score += 6; found.append(f"🎯 Prix {'sous BB' if buy else 'au-dessus BB'}")

    # ADX (6 pts)
    if med["adx"] > MIN_ADX:
        score += 3; found.append(f"💪 ADX={med['adx']:.0f}")
    if (med["pdi"]>med["ndi"]) if buy else (med["ndi"]>med["pdi"]):
        score += 3

    return score, found

# ══════════════════════════════════════════════════════════════
#  FILTRE NEWS
# ══════════════════════════════════════════════════════════════

def is_news_blackout(symbol: str) -> Tuple[bool, str]:
    now = datetime.now(timezone.utc)
    crypto = symbol.replace("/","") in ("BTCUSD","ETHUSD")
    if now.weekday() >= 5 and not crypto: return True, "Week-end"
    if now.weekday() >= 5: return False, ""
    if now.weekday() == 4 and 12 <= now.hour <= 13: return True, "NFP vendredi"
    if now.weekday() == 2 and 18 <= now.hour <= 19: return True, "FOMC mercredi"
    if now.weekday() == 1 and 14 <= now.hour <= 15: return True, "RBA mardi"
    if now.weekday() == 3 and 11 <= now.hour <= 12: return True, "BCE jeudi"
    return False, ""

# Calendrier fixe des news majeures (heure UTC)
NEWS_CALENDAR = [
    # (weekday, hour_start, hour_end, nom, impact, description)
    (4, 12, 13, "NFP 🇺🇸",      "🔴 FORT",   "Non-Farm Payrolls — donnée emploi américaine"),
    (2, 18, 19, "FOMC 🇺🇸",     "🔴 FORT",   "Décision taux d'intérêt Fed — très volatile"),
    (1, 14, 15, "RBA 🇦🇺",      "🟠 MOYEN",  "Décision taux Banque Centrale Australie"),
    (3, 11, 12, "BCE 🇪🇺",      "🔴 FORT",   "Décision taux Banque Centrale Européenne"),
    (0, 9,  10, "PMI EU 🇪🇺",   "🟠 MOYEN",  "Indice activité manufacturière Europe"),
    (4, 13, 14, "CPI USA 🇺🇸",  "🔴 FORT",   "Inflation américaine — impact majeur USD"),
    (2, 12, 13, "CPI UK 🇬🇧",   "🟠 MOYEN",  "Inflation britannique — impact GBP"),
    (3, 12, 13, "BOE 🇬🇧",      "🔴 FORT",   "Décision taux Banque Centrale Angleterre"),
    (1, 23, 24, "BOJ 🇯🇵",      "🟠 MOYEN",  "Décision taux Banque du Japon"),
    (4, 14, 15, "Retail 🇺🇸",   "🟡 FAIBLE", "Ventes au détail USA"),
    (2, 14, 15, "GDP 🇺🇸",      "🔴 FORT",   "PIB américain — croissance économique"),
]

def get_upcoming_news(hours_ahead: int = 2) -> list:
    """Retourne les news dans les prochaines X heures."""
    now = datetime.now(timezone.utc)
    upcoming = []
    for wd, h_start, h_end, name, impact, desc in NEWS_CALENDAR:
        if now.weekday() != wd:
            continue
        news_time = now.replace(hour=h_start, minute=0, second=0)
        diff = (news_time - now).total_seconds() / 3600
        if -0.5 <= diff <= hours_ahead:  # -30min à +X heures
            upcoming.append({
                "name":   name,
                "impact": impact,
                "desc":   desc,
                "heure":  f"{h_start:02d}h00 UTC",
                "minutes": int(diff * 60),
            })
    return upcoming

def news_impact_on_score(symbol: str) -> Tuple[int, str]:
    """
    Ne pénalise plus le score.
    Retourne juste une note informative si une news approche.
    """
    upcoming = get_upcoming_news(hours_ahead=3)
    if not upcoming:
        return 0, ""
    worst = upcoming[0]
    minutes = worst["minutes"]
    if minutes < 0:
        return 0, ""
    if "🔴" in worst["impact"]:
        return 0, f"⚠️ {worst['name']} dans {minutes}min — soyez prudent"
    elif "🟠" in worst["impact"]:
        return 0, f"📰 {worst['name']} dans {minutes}min"
    return 0, ""

def send_news_alert():
    """Envoie une alerte 30 min avant une news majeure."""
    upcoming = get_upcoming_news(hours_ahead=0.6)
    if not upcoming:
        return
    for news in upcoming:
        if news["minutes"] < 0 or news["minutes"] > 36:
            continue
        impact_emoji = "🚨" if "🔴" in news["impact"] else "⚠️"
        msg = (
            f"{impact_emoji} *ALERTE NEWS ÉCONOMIQUE*\n"
            f"{'═'*24}\n"
            f"📰 *{news['name']}*\n"
            f"⏰ Dans *{news['minutes']} minutes* ({news['heure']})\n"
            f"Impact : {news['impact']}\n"
            f"{'─'*24}\n"
            f"_{news['desc']}_\n"
            f"{'─'*24}\n"
            f"{'🚨 *VOLATILITÉ EXTRÊME ATTENDUE*' if '🔴' in news['impact'] else '⚠️ Volatilité possible'}\n"
            f"🛡️ _Réduisez vos positions ou fermez avant la news._\n"
            f"❌ _Aucun nouveau signal pendant cette période._\n"
            f"{'═'*24}"
        )
        telegram_send(msg)
        log.info(f"📰 Alerte news: {news['name']}")

def send_daily_news_calendar():
    """Envoie le calendrier économique du jour chaque matin."""
    now = datetime.now(timezone.utc)
    today_news = []

    for wd, h_start, h_end, name, impact, desc in NEWS_CALENDAR:
        if now.weekday() == wd:
            today_news.append((h_start, name, impact, desc))

    if not today_news:
        msg = (
            f"📅 *CALENDRIER ÉCONOMIQUE*\n"
            f"{'─'*24}\n"
            f"📆 {now.strftime('%A %d/%m/%Y').upper()}\n\n"
            f"✅ Pas de news majeures aujourd'hui\n"
            f"🟢 Conditions favorables pour trader !\n"
            f"{'─'*24}\n"
            f"🤖 _Bot actif — analyse en continu_"
        )
    else:
        lines = ""
        for h, name, impact, desc in sorted(today_news):
            lines += f"  {impact} *{name}* — `{h:02d}h00 UTC`\n  _{desc}_\n\n"

        msg = (
            f"📅 *CALENDRIER ÉCONOMIQUE DU JOUR*\n"
            f"{'═'*26}\n"
            f"📆 {now.strftime('%A %d/%m/%Y').upper()}\n\n"
            f"{lines}"
            f"{'─'*26}\n"
            f"⚠️ _Soyez prudents pendant ces créneaux._\n"
            f"🤖 _Le bot bloque les signaux automatiquement._\n"
            f"{'═'*26}"
        )
    telegram_send(msg)
    log.info("📅 Calendrier économique du jour envoyé")

def get_session() -> str:
    h = datetime.now(timezone.utc).hour
    if 7 <= h < 16:  return "🇪🇺 Session Européenne"
    if 12 <= h < 21: return "🇺🇸 Session Américaine"
    if 0 <= h < 9:   return "🇯🇵 Session Asiatique"
    return "😴 Marché calme"

# ══════════════════════════════════════════════════════════════
#  ANALYSE COMPLÈTE
# ══════════════════════════════════════════════════════════════

def analyze_symbol(symbol: str, scan_n: int) -> Optional[dict]:
    # Alterner timeframes pour économiser les requêtes
    if scan_n % 2 == 0:
        df_fast = fetch_ohlcv(symbol, "15min", 150); time.sleep(0.8)
        df_med  = fetch_ohlcv(symbol, "1h",   200);  time.sleep(0.8)
        df_slow = None
    else:
        df_fast = None
        df_med  = fetch_ohlcv(symbol, "1h",   200);  time.sleep(0.8)
        df_slow = fetch_ohlcv(symbol, "4h",   150);  time.sleep(0.8)

    if df_med is None: return None

    fast = analyze_tf(df_fast) if df_fast is not None else None
    med  = analyze_tf(df_med)
    slow = analyze_tf(df_slow) if df_slow is not None else None

    if not med: return None
    # Utiliser med comme fallback si fast ou slow manque
    if not fast: fast = med
    if not slow: slow = med

    # Direction consensus
    buy_pts = sum([
        med["ema20"] > med["ema50"],
        med["macd"]  > med["macd_s"],
        med["rsi"]   < 55,
        fast["rsi"]  < 50,
        fast["srsi"] < 50,
    ])
    sell_pts = sum([
        med["ema20"] < med["ema50"],
        med["macd"]  < med["macd_s"],
        med["rsi"]   > 45,
        fast["rsi"]  > 50,
        fast["srsi"] > 50,
    ])

    if buy_pts >= 3:    direction = "BUY"
    elif sell_pts >= 3: direction = "SELL"
    else: return None

    # SMC
    liq       = detect_liquidity(df_med)
    ob        = detect_order_block(df_med, direction)
    fvg       = detect_fvg(df_fast if df_fast is not None else df_med, direction)
    struct    = market_structure(df_med)
    choch_bos = detect_choch_bos(df_med)

    # Price Action
    patterns  = detect_candle_patterns(df_fast if df_fast is not None else df_med)

    # Sweep
    sweep_ok  = detect_sweep(df_fast if df_fast is not None else df_med, direction, liq)

    # Scores
    ind_score,  ind_conf  = indicator_score(fast, med, slow, direction)
    smc_s,      smc_conf  = smc_score(choch_bos, ob, fvg, liq, direction)
    pa_s,       pa_conf   = pa_score(patterns, direction)
    kl_score,   kl_conf   = check_key_levels(symbol, med["close"], direction)

    # Score total — sans pénalité news (juste affiché comme info)
    _, news_note = news_impact_on_score(symbol)
    total_score = ind_score + smc_s + pa_s + kl_score

    # Bonus/malus sweep
    if sweep_ok:
        total_score = min(total_score + 12, 100)
        sweep_label = "✅ Sweep confirmé — entrée optimale"
    else:
        total_score = max(total_score - 8, 0)
        sweep_label = "⚠️ Avant sweep — SL plus large"

    total_score = min(int(total_score), 100)

    if total_score < MIN_SCORE:
        log.info(f"{symbol}: score {total_score}/100 < {MIN_SCORE} — refusé")
        return None

    # Filtre news
    blackout, reason = is_news_blackout(symbol)
    if blackout:
        log.info(f"{symbol}: blackout ({reason})")
        return None

    # Prix
    price = fetch_price(symbol); time.sleep(0.5)
    if not price: price = med["close"]

    # SL intelligent
    atr_val = med["atr"]
    buffer  = atr_val * 0.2
    if direction == "BUY":
        if liq.get("buy_liquidity"):
            sl = liq["buy_liquidity"] - buffer
        elif ob:
            sl = ob["low"] - buffer
        else:
            sl = price - atr_val * 1.2
    else:
        if liq.get("sell_liquidity"):
            sl = liq["sell_liquidity"] + buffer
        elif ob:
            sl = ob["high"] + buffer
        else:
            sl = price + atr_val * 1.2

    sl_dist = abs(price - sl)
    if sl_dist < atr_val * 0.5:
        sl_dist = atr_val * 1.0
        sl = price - sl_dist if direction == "BUY" else price + sl_dist

    digits = get_digits(symbol)

    # Multi-TP
    tps = compute_multi_tp(price, sl, direction, total_score, digits)

    # Infos affichage
    zone     = premium_discount(df_med, price)
    session  = get_session()
    atr_pct  = (atr_val / price) * 100
    vol      = "🔥 HAUTE" if atr_pct > 0.5 else "📊 NORMALE" if atr_pct > 0.2 else "😴 BASSE"

    # DXY info
    _, dxy_note = get_dxy_bias(direction)

    # Toutes les confirmations
    all_conf = (ind_conf + smc_conf + pa_conf + kl_conf)[:6]
    if news_note:
        all_conf.append(news_note)

    clean = symbol.replace("/","")
    return {
        "symbol":      clean,
        "direction":   direction,
        "entry":       round(price, digits),
        "sl":          round(sl, digits),
        "tps":         tps,
        "score":       total_score,
        "confirmations": all_conf,
        "structure":   struct,
        "zone":        zone,
        "volatility":  vol,
        "sweep":       sweep_ok,
        "sweep_label": sweep_label,
        "dxy_note":    dxy_note,
        "rsi_h1":      round(med["rsi"], 1),
        "srsi":        round(fast["srsi"], 1),
        "wr":          round(fast["wr"], 1),
        "adx":         round(med["adx"], 1),
        "digits":      digits,
        "session":     session,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "message_id":  None,
        "closed":      False,
        "result":      None,
    }

def compute_multi_tp(entry: float, sl: float, direction: str,
                     score: int, digits: int) -> List[dict]:
    sl_dist = abs(entry - sl)
    ratios = [1.0, 1.5, 2.5, 4.0] if score >= 80 else \
             [1.0, 1.8, 3.0]       if score >= 70 else \
             [1.0, 2.0]
    tps = []
    for i, ratio in enumerate(ratios):
        dist = sl_dist * ratio
        price = entry + dist if direction == "BUY" else entry - dist
        tps.append({"level": i+1, "price": round(price, digits),
                    "ratio": ratio, "hit": False})
    return tps

# ══════════════════════════════════════════════════════════════
#  SURVEILLANCE TP/SL
# ══════════════════════════════════════════════════════════════

def check_active_signals():
    signals = load(SIGNALS_FILE)
    if not signals: return
    updated = False

    for key, s in list(signals.items()):
        if s.get("closed"): continue
        sym = s["symbol"]
        sym_fmt = sym[:3]+"/"+sym[3:]
        price = fetch_price(sym_fmt); time.sleep(0.5)
        if not price: continue

        msg_id = s.get("message_id")

        for tp in s["tps"]:
            if tp.get("hit"): continue
            tp_hit = price >= tp["price"] if s["direction"]=="BUY" else price <= tp["price"]
            if tp_hit:
                tp["hit"] = True; updated = True
                telegram_send(build_tp_msg(s, tp), reply_to=msg_id)
                log.info(f"[{sym}] ✅ TP{tp['level']} @ {price}")
                break

        sl_hit = price <= s["sl"] if s["direction"]=="BUY" else price >= s["sl"]
        if sl_hit:
            s["closed"] = True; s["result"] = "SL"
            s["close_time"] = datetime.now(timezone.utc).isoformat()
            updated = True
            telegram_send(build_sl_msg(s), reply_to=msg_id)
            log.info(f"[{sym}] ❌ SL @ {price}")
            history = load(HISTORY_FILE); history[key] = s
            save(HISTORY_FILE, history); continue

        if all(t.get("hit") for t in s["tps"]):
            s["closed"] = True; s["result"] = "TP"
            s["close_time"] = datetime.now(timezone.utc).isoformat()
            updated = True
            history = load(HISTORY_FILE); history[key] = s
            save(HISTORY_FILE, history)

    if updated: save(SIGNALS_FILE, signals)

# ══════════════════════════════════════════════════════════════
#  SCAN
# ══════════════════════════════════════════════════════════════

def scan_markets():
    # Rafraîchir cache 1x/jour
    today = datetime.now(timezone.utc).date()
    if cache["last_refresh"] != today:
        refresh_daily_cache()

    n = scan_counter["n"]
    scan_counter["n"] += 1

    log.info(f"🔍 Scan #{n} — {'M15+H1' if n%2==0 else 'H1+H4'}...")
    signals = load(SIGNALS_FILE)

    actifs = [s for s in signals.values() if not s.get("closed")]
    if len(actifs) >= MAX_ACTIFS:
        log.info(f"Max {MAX_ACTIFS} signaux actifs"); return

    for symbol in SYMBOLS:
        clean = symbol.replace("/","")
        if any(s["symbol"]==clean and not s.get("closed") for s in signals.values()):
            continue

        result = analyze_symbol(symbol, n)
        if result:
            log.info(f"✅ {result['symbol']} {result['direction']} | Score: {result['score']}/100 | TPs: {len(result['tps'])}")
            msg_id = telegram_send(build_signal_msg(result))
            result["message_id"] = msg_id
            key = f"{clean}_{int(time.time())}"
            signals[key] = result
            save(SIGNALS_FILE, signals)
            time.sleep(2)

            actifs = [s for s in signals.values() if not s.get("closed")]
            if len(actifs) >= MAX_ACTIFS: break
        else:
            log.info(f"{symbol}: pas de setup")

    log.info("✔️  Scan terminé\n")

# ══════════════════════════════════════════════════════════════
#  MESSAGES TELEGRAM
# ══════════════════════════════════════════════════════════════

def fp(val: float, d: int) -> str: return f"{val:.{d}f}"

def confluence_bar(score: int) -> str:
    f = round(score/10)
    return f"`{'█'*f}{'░'*(10-f)}` {score}%"

def build_signal_msg(s: dict) -> str:
    emoji  = "🟢" if s["direction"]=="BUY" else "🔴"
    action = "BUY" if s["direction"]=="BUY" else "SELL"
    arrow  = "📈" if s["direction"]=="BUY" else "📉"
    tp_lines = "".join([
        f"  ├─TP{t['level']} `{fp(t['price'],s['digits'])}` — R:R {t['ratio']}x {'─'*int(t['ratio'])}\n"
        for t in s["tps"]
    ])
    conf = "\n".join([f"  {c}" for c in s["confirmations"]])
    dxy  = f"\n  💵 {s['dxy_note']}" if s.get("dxy_note") else ""

    return (
        f"{'═'*26}\n"
        f"{emoji} *{s['symbol']} — {action}* {arrow}\n"
        f"{'═'*26}\n\n"
        f"🎯 *ENTRÉE :*   `{fp(s['entry'],s['digits'])}`\n"
        f"🛑 *STOP LOSS :* `{fp(s['sl'],s['digits'])}`\n\n"
        f"🏹 *TAKE PROFITS ({len(s['tps'])} TP)*\n"
        f"{tp_lines}\n"
        f"{'─'*26}\n"
        f"🧠 *CONFLUENCE* {confluence_bar(s['score'])}\n"
        f"  📊 RSI `{s['rsi_h1']}` | ⚡ StochRSI `{s['srsi']}` | 📉 W%R `{s['wr']}`\n"
        f"  💨 Volatilité : {s['volatility']} — {len(s['tps'])} TP\n"
        f"  ⚠️ Zone : {s['zone']}\n"
        f"  🏗️ Structure : {s['structure']}\n"
        f"  💧 {s['sweep_label']}{dxy}\n"
        f"{'─'*26}\n"
        f"{conf}\n"
        f"{'─'*26}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n"
        f"{s['session']}\n"
        f"{'═'*26}\n"
        f"⚠️ _Gérez votre risque._"
    )

def build_tp_msg(s: dict, tp: dict) -> str:
    is_last = tp["level"] == len(s["tps"])
    return (
        f"{'🏆' if is_last else '✅'} *TP{tp['level']} TOUCHÉ — {s['symbol']}*\n"
        f"{'─'*24}\n"
        f"Direction : *{s['direction']}*\n"
        f"Entrée :    `{fp(s['entry'],s['digits'])}`\n"
        f"✅ TP{tp['level']} : `{fp(tp['price'],s['digits'])}` (R:R {tp['ratio']}x)\n"
        f"{'─'*24}\n"
        f"{'🏆 *DERNIER TP TOUCHÉ !* 🎉' if is_last else '💰 *Partiels sécurisés !*'}\n"
        f"{'💪 Excellent résultat !' if is_last else '🔒 Déplacez le SL à l entrée.'}\n"
        f"{'─'*24}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

def build_sl_msg(s: dict) -> str:
    tps_hit = sum(1 for t in s["tps"] if t.get("hit"))
    partial = f"\n✅ {tps_hit} TP partiel(s) touchés" if tps_hit else ""
    return (
        f"❌ *STOP-LOSS ATTEINT — {s['symbol']}*\n"
        f"{'─'*24}\n"
        f"Direction : *{s['direction']}*\n"
        f"Entrée :    `{fp(s['entry'],s['digits'])}`\n"
        f"❌ SL :     `{fp(s['sl'],s['digits'])}`{partial}\n"
        f"{'─'*24}\n"
        f"📉 *Perte — Stop Loss atteint.*\n"
        f"💪 _Faire partie du jeu. On reste discipliné !_\n"
        f"{'─'*24}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

# ══════════════════════════════════════════════════════════════
#  RÉSUMÉS
# ══════════════════════════════════════════════════════════════

def _get_stats(days_back: int = 0, month: bool = False, year: bool = False):
    history = load(HISTORY_FILE)
    today   = datetime.now(timezone.utc).date()
    tp = sl = 0
    tps_total = 0
    best = {}

    for s in history.values():
        try: d = datetime.fromisoformat(s.get("close_time","")).date()
        except: continue

        if year   and d.year  != today.year:  continue
        if month  and (d.year != today.year or d.month != today.month): continue
        if days_back > 0 and (today - d).days > days_back: continue
        if not year and not month and days_back == 0 and d != today: continue

        sym = s["symbol"]
        if sym not in best: best[sym] = {"tp":0,"sl":0}
        tps_hit = sum(1 for t in s.get("tps",[]) if t.get("hit"))
        tps_total += tps_hit
        if s.get("result")=="TP": tp+=1; best[sym]["tp"]+=1
        else: sl+=1; best[sym]["sl"]+=1

    return tp, sl, tps_total, best

def daily_summary():
    tp, sl, tps_total, best = _get_stats()
    total = tp+sl
    if total == 0: return
    wr = tp/total*100
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    stars = "⭐"*min(int(wr/20),5)
    perf = "🏆 EXCELLENTE" if wr>=70 else "💪 BONNE" if wr>=55 else "📊 CORRECTE"
    lines = []
    for sym, v in best.items():
        if v["tp"]: lines.append(f"✅ {sym} ({v['tp']} TP)")
        if v["sl"]: lines.append(f"❌ {sym} ({v['sl']} SL)")

    msg = (
        f"📊 *RÉSUMÉ DU JOUR — {datetime.now().strftime('%d/%m/%Y')}*\n"
        f"{'─'*24}\n"
        f"✅ Signaux TP :      *{tp}*\n"
        f"❌ Signaux SL :      *{sl}*\n"
        f"🏹 Niveaux TP hit :  *{tps_total}*\n"
        f"🎯 Winrate :         *{wr:.0f}%* {stars}\n"
        f"{'─'*24}\n"
        f"Performance : {perf} SESSION\n"
        f"{'─'*24}\n"
        f"{chr(10).join(lines) if lines else 'Aucun signal clôturé'}\n"
        f"{'─'*24}\n"
        f"🤖 _Sniper V6 — PA | SMC | DXY | Niveaux clés_"
    )
    telegram_send(msg)

def weekly_summary():
    tp, sl, tps_total, best = _get_stats(days_back=7)
    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    msg = (
        f"📅 *BILAN HEBDOMADAIRE*\n"
        f"{'─'*24}\n"
        f"✅ TP : *{tp}* | ❌ SL : *{sl}* | 🏹 Niveaux : *{tps_total}*\n"
        f"🎯 Winrate : *{wr:.0f}%*\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"{'─'*24}\n"
        f"{'🔥 Semaine exceptionnelle !' if wr>=70 else '💪 Continuons !' if wr>=50 else '📚 On progresse !'}\n"
        f"_Nouvelle semaine, nouvelles opportunités !_ 🚀"
    )
    telegram_send(msg)

def monthly_summary():
    tp, sl, tps_total, best = _get_stats(month=True)
    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    mois = datetime.now().strftime("%B %Y")
    msg = (
        f"📆 *BILAN MENSUEL — {mois.upper()}*\n"
        f"{'═'*24}\n"
        f"✅ TP : *{tp}* | ❌ SL : *{sl}*\n"
        f"🏹 Niveaux TP touchés : *{tps_total}*\n"
        f"🎯 Winrate : *{wr:.0f}%*\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"{'─'*24}\n"
        f"{'🔥 MOIS EXCEPTIONNEL !' if wr>=70 else '💪 Bon mois !' if wr>=55 else '📚 On progresse !'}\n"
        f"_Merci pour votre confiance ce mois-ci !_ 🙏"
    )
    telegram_send(msg)

def yearly_summary():
    tp, sl, tps_total, best = _get_stats(year=True)
    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    msg = (
        f"🏆 *BILAN ANNUEL — {datetime.now().year}*\n"
        f"{'═'*26}\n"
        f"✅ TP : *{tp}* | ❌ SL : *{sl}*\n"
        f"🏹 Niveaux TP touchés : *{tps_total}*\n"
        f"🎯 Winrate annuel : *{wr:.0f}%*\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"{'─'*26}\n"
        f"{'🔥 ANNÉE EXCEPTIONNELLE !' if wr>=70 else '💪 Belle année !' if wr>=55 else '📚 On progresse chaque année !'}\n"
        f"_Merci pour votre fidélité !_ 🙏🚀"
    )
    telegram_send(msg)

# ══════════════════════════════════════════════════════════════
#  MESSAGES D'AMBIANCE
# ══════════════════════════════════════════════════════════════

def send_citation():   telegram_send(random.choice(CITATIONS))
def send_humour():     telegram_send(random.choice(HUMOUR))
def send_motivation(): telegram_send(random.choice(MOTIVATION))
def send_matin():      telegram_send(random.choice(MATIN))
def send_soir():       telegram_send(random.choice(SOIR))

def send_market_watch():
    signals = load(SIGNALS_FILE)
    actifs  = [s for s in signals.values() if not s.get("closed")]
    n       = len(actifs)
    if n == 0:
        telegram_send("⏳ *Market Watch.* Pas de signal actif — la patience paie.")
    else:
        lines = "\n".join([f"  → {s['symbol']} {s['direction']}" for s in actifs])
        telegram_send(
            f"📡 *MARKET WATCH*\n{'─'*20}\n{get_session()}\n"
            f"🔎 {n} signal(s) actif(s) :\n{lines}\n{'─'*20}\n"
            f"🕐 {datetime.now().strftime('%H:%M')} UTC"
        )

# ══════════════════════════════════════════════════════════════
#  TELEGRAM
# ══════════════════════════════════════════════════════════════

async def _send(text: str, reply_to: int = None) -> Optional[int]:
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=reply_to,
        read_timeout=30, write_timeout=30, connect_timeout=30,
    )
    return msg.message_id

def telegram_send(text: str, reply_to: int = None) -> Optional[int]:
    for attempt in range(3):
        try:
            return asyncio.run(_send(text, reply_to))
        except Exception as e:
            log.warning(f"Telegram {attempt+1}/3: {e}")
            time.sleep(5)
    log.error("❌ Telegram échoué")
    return None

# ══════════════════════════════════════════════════════════════
#  PERSISTANCE
# ══════════════════════════════════════════════════════════════

def load(path: str) -> dict:
    if os.path.exists(path):
        with open(path,"r") as f: return json.load(f)
    return {}

def save(path: str, data: dict):
    with open(path,"w") as f: json.dump(data, f, indent=2)

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("🚀 Sniper Bot V6 — Ultimate Edition — Démarrage...")

    # Chargement initial du cache
    refresh_daily_cache()

    # Signaux
    schedule.every(1).hours.do(scan_markets)
    schedule.every(5).minutes.do(check_active_signals)

    # News — alerte 30 min avant + calendrier quotidien
    schedule.every(30).minutes.do(send_news_alert)
    schedule.every().day.at("07:30").do(send_daily_news_calendar)

    # Résumés
    schedule.every().day.at("21:00").do(daily_summary)
    schedule.every().monday.at("08:00").do(weekly_summary)
    schedule.every().day.at("09:00").do(
        lambda: monthly_summary() if datetime.now().day == 1 else None)
    schedule.every().day.at("20:00").do(
        lambda: yearly_summary() if (datetime.now().month == 12 and datetime.now().day == 31) else None)

    # Canal
    schedule.every().day.at("07:00").do(send_matin)
    schedule.every().day.at("21:30").do(send_soir)
    schedule.every().day.at("08:00").do(send_citation)
    schedule.every().day.at("19:00").do(send_citation)
    schedule.every().day.at("12:00").do(send_motivation)
    schedule.every().day.at("09:00").do(send_market_watch)
    schedule.every().day.at("14:00").do(send_market_watch)
    schedule.every().day.at("18:00").do(send_market_watch)
    schedule.every().wednesday.at("20:00").do(send_humour)
    schedule.every().friday.at("17:00").do(send_humour)

    scan_markets()

    log.info("✅ V6 actif — PA | SMC CHoCH/BOS | DXY | Niveaux clés | Multi-TP")
    while True:
        schedule.run_pending()
        time.sleep(30)
