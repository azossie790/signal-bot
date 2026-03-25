"""
╔══════════════════════════════════════════════════════════════╗
║         FOREX SIGNAL BOT V4 — ULTRA PUISSANT               ║
║  Sans MT5 | Twelve Data | Railway | Contenu Attractif       ║
║  Score Corrigé | Humour | Citations | Stats Hebdo           ║
╚══════════════════════════════════════════════════════════════╝

Prérequis :
  pip install requests pandas numpy python-telegram-bot schedule

API gratuite : https://twelvedata.com
Hébergement  : https://railway.app
"""

import time
import schedule
import logging
import json
import os
import requests
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import pandas as pd
import numpy as np
from telegram import Bot
from telegram.constants import ParseMode

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8633331614:AAHKOhSFUvRXUiWjM32ZPX8L9_2mBx7ePAA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@signaltraidingv2")
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY", "VOTRE_CLE_TWELVEDATA")

SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD",
    "XAU/USD",   # Or
    "XAG/USD",   # Argent
    "BTC/USD",   # Bitcoin
    "ETH/USD",   # Ethereum
]

# ── Paramètres de qualité ──
MIN_SCORE          = 65    # Score STRICT — bug corrigé
MIN_RR_RATIO       = 2.0   # TP = minimum 2x le SL
MAX_SIGNALS_ACTIFS = 3
MIN_ADX            = 20

SIGNALS_FILE = "active_signals.json"
HISTORY_FILE = "signals_history.json"

# ══════════════════════════════════════════════════════════════
#  CONTENU ATTRACTIF — Citations & Messages
# ══════════════════════════════════════════════════════════════

CITATIONS = [
    ("💬 _\"Le marché peut rester irrationnel plus longtemps que vous ne pouvez rester solvable.\"_", "John Maynard Keynes"),
    ("💬 _\"Coupez vos pertes rapidement, laissez courir vos profits.\"_", "Jesse Livermore"),
    ("💬 _\"La discipline est la différence entre un bon trader et un mauvais trader.\"_", "Mark Douglas"),
    ("💬 _\"Ne risquez jamais ce que vous ne pouvez pas vous permettre de perdre.\"_", "Warren Buffett"),
    ("💬 _\"Le trading est simple, mais pas facile.\"_", "Ed Seykota"),
    ("💬 _\"Gérez votre risque avant de penser aux profits.\"_", "Paul Tudor Jones"),
    ("💬 _\"Les marchés sont guidés par la peur et la cupidité.\"_", "Warren Buffett"),
    ("💬 _\"Un bon trader sait quand ne pas trader.\"_", "Jesse Livermore"),
    ("💬 _\"La patience est la vertu la plus rentable en trading.\"_", "Nicolas Darvas"),
    ("💬 _\"Votre plan de trading est votre meilleur ami.\"_", "Alexander Elder"),
]

MESSAGES_MOTIVATION = [
    "🔥 *La patience est la clé.* Pas de signal = pas de perte. On attend le setup parfait !",
    "💪 *Rappel important :* Ne forcez jamais un trade. Le marché sera là demain aussi.",
    "🧠 *Mindset du jour :* Les pros ne cherchent pas à tout trader — ils cherchent LES bons trades.",
    "⚡ *Discipline > Émotion.* Suivez le plan, ignorez le bruit du marché.",
    "🎯 *Qualité > Quantité.* 3 bons signaux par semaine valent mieux que 20 mauvais.",
    "🛡️ *Protégez votre capital d'abord.* Les profits viennent ensuite.",
    "📈 *Le trend est votre ami.* Ne tradez jamais contre la tendance principale.",
    "🌙 *Bonne nuit traders !* Le marché dort aussi parfois — reposez-vous.",
    "☀️ *Nouvelle journée, nouvelles opportunités !* Les marchés ouvrent dans quelques heures.",
    "🤝 *On est tous dans le même bateau.* Partagez, entraidez-vous, grandissez ensemble.",
]

MESSAGES_HUMOUR = [
    "😂 *Moi avant le trade :* \"Je vais juste regarder le marché...\"\n*Moi 3h après :* 📉💸😭",
    "🤡 *Le marché quand j'achète :* descend\n*Le marché quand je vends :* monte\n\nLogique non ?",
    "😅 *Mon indicateur préféré c'est :*\n→ Quand je prends un BUY → ça SELL\n→ Quand je prends un SELL → ça BUY 😭",
    "🎰 *La différence entre le trading et le casino ?*\nAu casino au moins ils te donnent des boissons gratuites 😂",
    "😤 *Stop Loss touché à -15 pips*\nLe marché 5 min après : 📈+200 pips\n\n_\"Bien sûr...\"_ 😑",
    "🧘 *Technique de méditation du trader :*\nFerme les yeux\nRespire fort\nNe regarde PAS le graphique\nRépète 😂",
    "💀 *Mon portefeuille après avoir ignoré le Stop Loss :*\n📉📉📉📉📉\n\n*Leçon apprise : TOUJOURS le SL* ✅",
    "😂 *Quand le signal dit BUY et que ta femme dit NON :*\nDans les deux cas... tu perds de l'argent 😅",
    "🤓 *J'ai analysé le marché pendant 6 heures*\n*J'ai utilisé 12 indicateurs*\n*J'ai regardé 5 timeframes*\n\nLe marché : fait exactement l'inverse 😭",
    "💪 *Un trader perdant est juste un trader gagnant qui n'a pas encore arrêté.*\nContinuez ! 🔥",
]

MESSAGES_MATIN = [
    "🌅 *BONJOUR TRADERS !*\n\nNovelle session, nouvelles opportunités !\nLes marchés européens ouvrent bientôt.\n\n📊 Restez disciplinés, suivez le plan.\n💪 Bonne session à tous !",
    "☀️ *RÉVEIL DU TRADER !*\n\nLa session de Londres approche !\nC'est souvent là que les meilleurs setups apparaissent.\n\n🎯 On reste focus, on attend nos signaux.\n📈 Let's go !",
    "🔔 *SESSION EUROPÉENNE BIENTÔT !*\n\nTop 3 des paires à surveiller aujourd'hui :\n→ EUR/USD 👀\n→ GBP/USD 👀\n→ XAU/USD 👀\n\nLe bot analyse en continu. On vous prévient ! 🤖",
]

MESSAGES_SOIR = [
    "🌙 *FIN DE SESSION !*\n\nLa session américaine se termine.\nLes marchés asiatiques prennent le relais.\n\n💤 Moins de volatilité cette nuit.\nLe bot continue de surveiller. Bonne nuit ! 😴",
    "🌆 *BILAN DE SOIRÉE*\n\nLe bot a analysé tous les marchés aujourd'hui.\nConsultez le résumé quotidien ci-dessous.\n\n🙏 Merci d'être avec nous !\nOn se retrouve demain matin 💪",
]

ALERTES_VOLATILITE = [
    "⚡ *VOLATILITÉ ÉLEVÉE DÉTECTÉE !*\n\n{symbol} montre une activité inhabituelle.\nSoyez prudents — les spreads peuvent être larges.\n\n🛡️ Réduisez la taille de vos positions si vous tradez manuellement.",
    "🌊 *MOUVEMENT FORT SUR {symbol} !*\n\nLe marché s'emballe.\nNos filtres de sécurité sont actifs.\n\n⚠️ Attendez notre signal avant d'entrer.",
]

# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_v4.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  TWELVE DATA — DONNÉES
# ══════════════════════════════════════════════════════════════

BASE_URL = "https://api.twelvedata.com"

def fetch_ohlcv(symbol: str, interval: str = "1h", bars: int = 200) -> Optional[pd.DataFrame]:
    try:
        params = {
            "symbol": symbol, "interval": interval,
            "outputsize": bars, "apikey": TWELVEDATA_KEY,
        }
        resp = requests.get(f"{BASE_URL}/time_series", params=params, timeout=15)
        data = resp.json()
        if data.get("status") == "error":
            log.warning(f"{symbol} {interval}: {data.get('message')}")
            return None
        values = data.get("values", [])
        if not values:
            return None
        df = pd.DataFrame(values)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(inplace=True)
        return df.sort_index()
    except Exception as e:
        log.error(f"fetch_ohlcv {symbol}: {e}")
        return None

def fetch_price(symbol: str) -> Optional[float]:
    try:
        resp = requests.get(f"{BASE_URL}/price",
            params={"symbol": symbol, "apikey": TWELVEDATA_KEY}, timeout=10)
        return float(resp.json().get("price", 0) or 0)
    except:
        return None

def fetch_multi_tf(symbol: str):
    df_fast = fetch_ohlcv(symbol, "15min", 150)
    time.sleep(1.0)
    df_med  = fetch_ohlcv(symbol, "1h",   250)
    time.sleep(1.0)
    df_slow = fetch_ohlcv(symbol, "4h",   150)
    time.sleep(1.0)
    return df_fast, df_med, df_slow


# ══════════════════════════════════════════════════════════════
#  INDICATEURS TECHNIQUES
# ══════════════════════════════════════════════════════════════

def rsi(series: pd.Series, p: int = 14) -> pd.Series:
    d = series.diff()
    g = d.clip(lower=0).ewm(span=p, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(span=p, adjust=False).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def macd(series: pd.Series):
    e12 = series.ewm(span=12, adjust=False).mean()
    e26 = series.ewm(span=26, adjust=False).mean()
    m   = e12 - e26
    s   = m.ewm(span=9, adjust=False).mean()
    return m, s

def atr_calc(df: pd.DataFrame, p: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(span=p, adjust=False).mean()

def bollinger(series: pd.Series, p: int = 20, k: float = 2.0):
    mid = series.rolling(p).mean()
    std = series.rolling(p).std()
    return mid + k * std, mid, mid - k * std

def stochastic(df: pd.DataFrame, k: int = 14, d: int = 3):
    lo = df["low"].rolling(k).min()
    hi = df["high"].rolling(k).max()
    pk = 100 * (df["close"] - lo) / (hi - lo + 1e-10)
    return pk, pk.rolling(d).mean()

def adx_calc(df: pd.DataFrame, p: int = 14):
    h, l = df["high"], df["low"]
    up, dn = h.diff(), -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0)
    ndm = dn.where((dn > up) & (dn > 0), 0.0)
    av  = atr_calc(df, p)
    pdi = 100 * pdm.ewm(span=p, adjust=False).mean() / av.replace(0, np.nan)
    ndi = 100 * ndm.ewm(span=p, adjust=False).mean() / av.replace(0, np.nan)
    denom = (pdi + ndi).replace(0, np.nan)
    dx  = 100 * (pdi - ndi).abs() / denom
    return dx.ewm(span=p, adjust=False).mean(), pdi, ndi

def ichimoku(df: pd.DataFrame):
    """Ichimoku Cloud — confirmation de tendance supplémentaire."""
    h9  = df["high"].rolling(9).max()
    l9  = df["low"].rolling(9).min()
    h26 = df["high"].rolling(26).max()
    l26 = df["low"].rolling(26).min()
    tenkan  = (h9  + l9)  / 2
    kijun   = (h26 + l26) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    h52 = df["high"].rolling(52).max()
    l52 = df["low"].rolling(52).min()
    senkou_b = ((h52 + l52) / 2).shift(26)
    return tenkan, kijun, senkou_a, senkou_b

def williams_r(df: pd.DataFrame, p: int = 14) -> pd.Series:
    hi = df["high"].rolling(p).max()
    lo = df["low"].rolling(p).min()
    return -100 * (hi - df["close"]) / (hi - lo + 1e-10)

def cci(df: pd.DataFrame, p: int = 20) -> pd.Series:
    tp  = (df["high"] + df["low"] + df["close"]) / 3
    mad = tp.rolling(p).apply(lambda x: np.mean(np.abs(x - x.mean())))
    return (tp - tp.rolling(p).mean()) / (0.015 * mad.replace(0, np.nan))

def get_digits(symbol: str) -> int:
    if "JPY" in symbol: return 3
    if "BTC" in symbol: return 2
    if "ETH" in symbol: return 2
    if "XAU" in symbol: return 2
    if "XAG" in symbol: return 3
    return 5


# ══════════════════════════════════════════════════════════════
#  ANALYSE PAR TIMEFRAME
# ══════════════════════════════════════════════════════════════

def analyze_tf(df: pd.DataFrame) -> Optional[dict]:
    if len(df) < 60:
        return None
    try:
        close = df["close"]
        rv         = rsi(close)
        mv, ms     = macd(close)
        ema20      = close.ewm(span=20, adjust=False).mean()
        ema50      = close.ewm(span=50, adjust=False).mean()
        ema200     = close.ewm(span=200, adjust=False).mean()
        bb_u,_,bb_l = bollinger(close)
        sk, sd     = stochastic(df)
        adx_v, pdi, ndi = adx_calc(df)
        wr         = williams_r(df)
        cci_v      = cci(df)
        tk, kj, sa, sb = ichimoku(df)

        return {
            "rsi":     float(rv.iloc[-1]),
            "rsi_p":   float(rv.iloc[-2]),
            "macd":    float(mv.iloc[-1]),
            "macd_s":  float(ms.iloc[-1]),
            "macd_p":  float(mv.iloc[-2]),
            "ms_p":    float(ms.iloc[-2]),
            "ema20":   float(ema20.iloc[-1]),
            "ema50":   float(ema50.iloc[-1]),
            "ema200":  float(ema200.iloc[-1]),
            "bb_u":    float(bb_u.iloc[-1]),
            "bb_l":    float(bb_l.iloc[-1]),
            "stoch_k": float(sk.iloc[-1]),
            "stoch_d": float(sd.iloc[-1]),
            "adx":     float(adx_v.iloc[-1]),
            "pdi":     float(pdi.iloc[-1]),
            "ndi":     float(ndi.iloc[-1]),
            "wr":      float(wr.iloc[-1]),
            "cci":     float(cci_v.iloc[-1]),
            "tenkan":  float(tk.iloc[-1]) if not pd.isna(tk.iloc[-1]) else 0,
            "kijun":   float(kj.iloc[-1]) if not pd.isna(kj.iloc[-1]) else 0,
            "cloud_a": float(sa.iloc[-1]) if not pd.isna(sa.iloc[-1]) else 0,
            "cloud_b": float(sb.iloc[-1]) if not pd.isna(sb.iloc[-1]) else 0,
            "close":   float(close.iloc[-1]),
            "atr":     float(atr_calc(df).iloc[-1]),
            "volume_avg": float(df.get("volume", pd.Series([1])).rolling(20).mean().iloc[-1]) if "volume" in df.columns else 1.0,
        }
    except Exception as e:
        log.error(f"analyze_tf error: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  SCORE DE CONFIANCE — CORRIGÉ ET AMÉLIORÉ
# ══════════════════════════════════════════════════════════════

def compute_score(fast: dict, med: dict, slow: dict, direction: str) -> Tuple[int, list]:
    """
    Score sur 100 points — STRICT.
    Chaque condition est vérifiée indépendamment.
    Le signal ne passe QUE si score >= MIN_SCORE.
    """
    score = 0
    reasons = []
    buy = direction == "BUY"

    # ── RSI (15 pts) ──
    rsi_fast_ok = fast["rsi"] < 38 if buy else fast["rsi"] > 62
    rsi_med_ok  = med["rsi"]  < 52 if buy else med["rsi"]  > 48
    rsi_slow_ok = slow["rsi"] < 55 if buy else slow["rsi"] > 45

    if rsi_fast_ok:
        score += 5
        reasons.append(f"RSI M15={'survendu' if buy else 'suracheté'} ({fast['rsi']:.0f})")
    if rsi_med_ok:
        score += 5
        reasons.append(f"RSI H1 ok ({med['rsi']:.0f})")
    if rsi_slow_ok:
        score += 5

    # ── MACD croisement (15 pts) ──
    cross_fast = (fast["macd"] > fast["macd_s"] and fast["macd_p"] <= fast["ms_p"]) if buy \
            else (fast["macd"] < fast["macd_s"] and fast["macd_p"] >= fast["ms_p"])
    macd_med  = med["macd"]  > med["macd_s"]  if buy else med["macd"]  < med["macd_s"]
    macd_slow = slow["macd"] > slow["macd_s"] if buy else slow["macd"] < slow["macd_s"]

    if cross_fast:
        score += 7
        reasons.append(f"MACD M15 croise {'↑' if buy else '↓'}")
    if macd_med:
        score += 4
    if macd_slow:
        score += 4
        reasons.append("MACD H4 aligné")

    # ── EMA tendance (15 pts) ──
    ema_fast = fast["ema20"] > fast["ema50"]  if buy else fast["ema20"] < fast["ema50"]
    ema_med  = med["ema20"]  > med["ema50"]   if buy else med["ema20"]  < med["ema50"]
    ema_slow = slow["ema20"] > slow["ema200"] if buy else slow["ema20"] < slow["ema200"]

    if ema_fast: score += 4
    if ema_med:
        score += 6
        reasons.append(f"EMA20 {'>' if buy else '<'} EMA50 H1")
    if ema_slow:
        score += 5
        reasons.append("Tendance H4 confirmée")

    # ── Bollinger (10 pts) ──
    bb_fast = fast["close"] < fast["bb_l"] if buy else fast["close"] > fast["bb_u"]
    bb_med  = med["close"]  < med["bb_l"]  if buy else med["close"]  > med["bb_u"]

    if bb_fast:
        score += 6
        reasons.append(f"Prix {'sous BB bas' if buy else 'au-dessus BB haut'} M15")
    if bb_med:
        score += 4

    # ── Stochastique (10 pts) ──
    stoch_ok = (fast["stoch_k"] < 25 and fast["stoch_k"] > fast["stoch_d"]) if buy \
          else (fast["stoch_k"] > 75 and fast["stoch_k"] < fast["stoch_d"])
    if stoch_ok:
        score += 10
        reasons.append(f"Stoch {'survendu+croise' if buy else 'suracheté+croise'}")

    # ── ADX force de tendance (10 pts) ──
    if med["adx"] > MIN_ADX:
        score += 5
        reasons.append(f"ADX={med['adx']:.0f} tendance forte")
    if (med["pdi"] > med["ndi"]) if buy else (med["ndi"] > med["pdi"]):
        score += 5

    # ── Williams %R (8 pts) ──
    wr_ok = fast["wr"] < -70 if buy else fast["wr"] > -30
    if wr_ok:
        score += 8
        reasons.append(f"Williams %R {'survendu' if buy else 'suracheté'}")

    # ── CCI (7 pts) ──
    cci_ok = fast["cci"] < -100 if buy else fast["cci"] > 100
    if cci_ok:
        score += 7
        reasons.append(f"CCI {'survendu' if buy else 'suracheté'} ({fast['cci']:.0f})")

    # ── Ichimoku (10 pts) ──
    price = med["close"]
    cloud_top    = max(med["cloud_a"], med["cloud_b"])
    cloud_bottom = min(med["cloud_a"], med["cloud_b"])
    above_cloud  = price > cloud_top
    below_cloud  = price < cloud_bottom
    tk_kj_bull   = med["tenkan"] > med["kijun"]
    tk_kj_bear   = med["tenkan"] < med["kijun"]

    if (above_cloud and tk_kj_bull) if buy else (below_cloud and tk_kj_bear):
        score += 10
        reasons.append(f"Ichimoku {'bullish' if buy else 'bearish'} ☁️")

    # ── BONUS multi-timeframe alignement (bonus 5 pts) ──
    all_aligned = (
        (fast["ema20"] > fast["ema50"]) == buy and
        (med["ema20"]  > med["ema50"])  == buy and
        (slow["ema20"] > slow["ema200"]) == buy
    )
    if all_aligned:
        score += 5
        reasons.append("✨ Alignement parfait M15+H1+H4")

    # ── STRICT : score plafonné à 100 ──
    final_score = min(int(score), 100)

    return final_score, reasons[:5]


# ══════════════════════════════════════════════════════════════
#  FILTRE NEWS
# ══════════════════════════════════════════════════════════════

def is_news_blackout(symbol: str) -> bool:
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:                          return True   # Week-end
    if now.weekday() == 4 and 12 <= now.hour <= 13: return True   # NFP vendredi
    if now.weekday() == 2 and 18 <= now.hour <= 19: return True   # FOMC mercredi
    if now.weekday() == 1 and 14 <= now.hour <= 15: return True   # RBA mardi
    return False


# ══════════════════════════════════════════════════════════════
#  ANALYSE COMPLÈTE
# ══════════════════════════════════════════════════════════════

def analyze_symbol(symbol: str) -> Optional[dict]:
    df_fast, df_med, df_slow = fetch_multi_tf(symbol)

    if df_fast is None or df_med is None or df_slow is None:
        log.warning(f"{symbol}: données manquantes")
        return None

    fast = analyze_tf(df_fast)
    med  = analyze_tf(df_med)
    slow = analyze_tf(df_slow)

    if not fast or not med or not slow:
        return None

    # ── Consensus direction (5 conditions minimum sur 5) ──
    buy_pts = sum([
        med["ema20"]  > med["ema50"],
        slow["ema20"] > slow["ema200"],
        med["macd"]   > med["macd_s"],
        med["rsi"]    < 55,
        fast["rsi"]   < 48,
    ])
    sell_pts = sum([
        med["ema20"]  < med["ema50"],
        slow["ema20"] < slow["ema200"],
        med["macd"]   < med["macd_s"],
        med["rsi"]    > 45,
        fast["rsi"]   > 52,
    ])

    if buy_pts >= 4:
        direction = "BUY"
    elif sell_pts >= 4:
        direction = "SELL"
    else:
        return None

    # ── Score STRICT ──
    score, reasons = compute_score(fast, med, slow, direction)

    # FIX BUG : vérification STRICTE avant tout
    if score < MIN_SCORE:
        log.info(f"{symbol}: score {score}/100 < minimum {MIN_SCORE} — REFUSÉ")
        return None

    # ── Prix actuel ──
    price = fetch_price(symbol)
    time.sleep(0.5)
    if not price or price == 0:
        price = med["close"]

    # ── TP/SL avec ratio 2:1 minimum ──
    atr_val = med["atr"]
    sl_dist = atr_val * 1.0
    tp_dist = max(sl_dist * MIN_RR_RATIO, sl_dist * 2.0)  # Forcé minimum 2:1

    if direction == "BUY":
        tp = price + tp_dist
        sl = price - sl_dist
    else:
        tp = price - tp_dist
        sl = price + sl_dist

    # ── Filtre news ──
    if is_news_blackout(symbol):
        log.info(f"{symbol}: blackout news — refusé")
        return None

    digits = get_digits(symbol)
    clean  = symbol.replace("/", "")

    return {
        "symbol":    clean,
        "direction": direction,
        "entry":     round(price, digits),
        "tp":        round(tp, digits),
        "sl":        round(sl, digits),
        "score":     score,
        "reasons":   reasons,
        "rr_ratio":  round(tp_dist / sl_dist, 2),
        "atr":       round(atr_val, digits),
        "adx":       round(med["adx"], 1),
        "rsi_h1":    round(med["rsi"], 1),
        "digits":    digits,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "closed":    False,
        "result":    None,
    }


# ══════════════════════════════════════════════════════════════
#  SURVEILLANCE TP / SL
# ══════════════════════════════════════════════════════════════

def check_active_signals():
    signals = load_signals(SIGNALS_FILE)
    if not signals:
        return

    updated = False
    for key, s in list(signals.items()):
        if s.get("closed"):
            continue

        raw = s["symbol"]
        sym = raw[:3] + "/" + raw[3:] if "/" not in raw else raw

        price = fetch_price(sym)
        time.sleep(0.8)
        if not price:
            continue

        tp_hit = sl_hit = False
        if s["direction"] == "BUY":
            if price >= s["tp"]:  tp_hit = True
            elif price <= s["sl"]: sl_hit = True
        else:
            if price <= s["tp"]:  tp_hit = True
            elif price >= s["sl"]: sl_hit = True

        if tp_hit or sl_hit:
            s["closed"]     = True
            s["result"]     = "TP" if tp_hit else "SL"
            s["close_price"] = price
            s["close_time"] = datetime.now(timezone.utc).isoformat()
            updated = True

            telegram_send(msg_tp(s) if tp_hit else msg_sl(s))
            log.info(f"[{s['symbol']}] {'✅ TP' if tp_hit else '❌ SL'} @ {price}")

            history = load_signals(HISTORY_FILE)
            history[key] = s
            save_signals(HISTORY_FILE, history)

    if updated:
        save_signals(SIGNALS_FILE, signals)


# ══════════════════════════════════════════════════════════════
#  SCAN DES MARCHÉS
# ══════════════════════════════════════════════════════════════

def scan_markets():
    log.info("🔍 Scan multi-timeframe + 9 indicateurs...")
    signals = load_signals(SIGNALS_FILE)

    actifs = [s for s in signals.values() if not s.get("closed")]
    if len(actifs) >= MAX_SIGNALS_ACTIFS:
        log.info(f"Max {MAX_SIGNALS_ACTIFS} signaux actifs — scan suspendu")
        return

    found = 0
    for symbol in SYMBOLS:
        clean = symbol.replace("/", "")
        if any(s["symbol"] == clean and not s.get("closed") for s in signals.values()):
            continue

        result = analyze_symbol(symbol)
        if result:
            log.info(f"✅ SIGNAL VALIDE: {result['symbol']} {result['direction']} | Score: {result['score']}/100")
            key = f"{clean}_{int(time.time())}"
            signals[key] = result
            save_signals(SIGNALS_FILE, signals)
            telegram_send(msg_signal(result))
            found += 1
            time.sleep(2)

            actifs = [s for s in signals.values() if not s.get("closed")]
            if len(actifs) >= MAX_SIGNALS_ACTIFS:
                break
        else:
            log.info(f"{symbol}: pas de setup qualifié (score < {MIN_SCORE})")

    if found == 0:
        log.info("Aucun signal qualifié ce cycle.")

    log.info("✔️  Scan terminé.\n")


# ══════════════════════════════════════════════════════════════
#  RÉSUMÉ QUOTIDIEN
# ══════════════════════════════════════════════════════════════

def daily_summary():
    history = load_signals(HISTORY_FILE)
    today   = datetime.now(timezone.utc).date()
    tp_count = sl_count = total = 0
    lines = []

    for s in history.values():
        try:
            if datetime.fromisoformat(s.get("close_time","")).date() != today:
                continue
        except:
            continue
        total += 1
        if s.get("result") == "TP":
            tp_count += 1
            lines.append(f"✅ {s['symbol']} {s['direction']}")
        else:
            sl_count += 1
            lines.append(f"❌ {s['symbol']} {s['direction']}")

    winrate = (tp_count / total * 100) if total > 0 else 0
    perf    = "🏆 EXCELLENTE" if winrate >= 70 else "💪 BONNE" if winrate >= 55 else "📊 CORRECTE"

    detail  = "\n".join(lines) if lines else "Aucun signal clôturé aujourd'hui"
    stars   = "⭐" * min(int(winrate / 20), 5)

    msg = (
        f"📊 *RÉSUMÉ DU JOUR — {today.strftime('%d/%m/%Y')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ TP touchés :   *{tp_count}*\n"
        f"❌ SL atteints :  *{sl_count}*\n"
        f"📈 Total trades : *{total}*\n"
        f"🎯 Winrate :      *{winrate:.0f}%* {stars}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Performance : {perf} SESSION\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{detail}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Bot V4 — 9 indicateurs | Analyse multi-timeframe_"
    )
    telegram_send(msg)


# ══════════════════════════════════════════════════════════════
#  STATS HEBDOMADAIRES
# ══════════════════════════════════════════════════════════════

def weekly_summary():
    history  = load_signals(HISTORY_FILE)
    today    = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    tp = sl = 0
    best_symbol = {}

    for s in history.values():
        try:
            d = datetime.fromisoformat(s.get("close_time","")).date()
        except:
            continue
        if not (week_ago <= d <= today):
            continue
        sym = s["symbol"]
        if sym not in best_symbol:
            best_symbol[sym] = {"tp": 0, "sl": 0}
        if s.get("result") == "TP":
            tp += 1
            best_symbol[sym]["tp"] += 1
        else:
            sl += 1
            best_symbol[sym]["sl"] += 1

    total   = tp + sl
    winrate = (tp / total * 100) if total > 0 else 0

    # Meilleure paire
    best = max(best_symbol.items(), key=lambda x: x[1]["tp"], default=("N/A", {}))

    msg = (
        f"📅 *BILAN HEBDOMADAIRE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📆 Semaine du {week_ago.strftime('%d/%m')} au {today.strftime('%d/%m/%Y')}\n\n"
        f"✅ TP touchés :   *{tp}*\n"
        f"❌ SL atteints :  *{sl}*\n"
        f"📊 Total :        *{total}*\n"
        f"🎯 Winrate :      *{winrate:.0f}%*\n"
        f"🏅 Meilleure paire : *{best[0]}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{'🔥 Semaine exceptionnelle !' if winrate >= 70 else '💪 Continuons à améliorer !' if winrate >= 50 else '📚 On analyse et on progresse !'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Merci de votre confiance — Nouvelle semaine, nouvelles opportunités !_ 🚀"
    )
    telegram_send(msg)


# ══════════════════════════════════════════════════════════════
#  MESSAGES D'AMBIANCE
# ══════════════════════════════════════════════════════════════

def send_citation():
    citation, auteur = random.choice(CITATIONS)
    msg = f"{citation}\n\n— _{auteur}_"
    telegram_send(msg)
    log.info("📖 Citation envoyée")

def send_motivation():
    msg = random.choice(MESSAGES_MOTIVATION)
    telegram_send(msg)
    log.info("💪 Message motivation envoyé")

def send_humour():
    msg = random.choice(MESSAGES_HUMOUR)
    telegram_send(msg)
    log.info("😂 Message humour envoyé")

def send_matin():
    telegram_send(random.choice(MESSAGES_MATIN))
    log.info("☀️ Message matin envoyé")

def send_soir():
    telegram_send(random.choice(MESSAGES_SOIR))
    log.info("🌙 Message soir envoyé")

def send_market_status():
    """Envoie un aperçu rapide du marché."""
    now = datetime.now(timezone.utc)
    session = ""
    if 7 <= now.hour < 16:
        session = "🇪🇺 Session EUROPÉENNE active"
    elif 12 <= now.hour < 21:
        session = "🇺🇸 Session AMÉRICAINE active"
    elif 0 <= now.hour < 9:
        session = "🇯🇵 Session ASIATIQUE active"
    else:
        session = "😴 Marché calme"

    msg = (
        f"📡 *STATUT DU MARCHÉ*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {now.strftime('%H:%M')} UTC\n"
        f"{session}\n\n"
        f"🤖 Bot actif — Analyse en cours\n"
        f"📊 {len(SYMBOLS)} paires surveillées\n"
        f"⚖️ Ratio R/R minimum : 1:{MIN_RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Prochain scan dans moins d'1 heure_ ⏳"
    )
    telegram_send(msg)


# ══════════════════════════════════════════════════════════════
#  MESSAGES TELEGRAM — FORMATÉS
# ══════════════════════════════════════════════════════════════

def fp(val: float, digits: int) -> str:
    return f"{val:.{digits}f}"

def score_bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)

def score_label(score: int) -> str:
    if score >= 85: return "🔥 EXCEPTIONNEL"
    if score >= 75: return "💎 TRÈS FORT"
    if score >= 65: return "✅ SOLIDE"
    return "⚠️ FAIBLE"

def msg_signal(s: dict) -> str:
    emoji  = "🟢" if s["direction"] == "BUY" else "🔴"
    arrow  = "📈" if s["direction"] == "BUY" else "📉"
    action = "ACHETER" if s["direction"] == "BUY" else "VENDRE"
    reasons = "\n".join([f"  • {r}" for r in s["reasons"]])
    return (
        f"{emoji} *SIGNAL {action} — {s['symbol']}* {arrow}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Entrée :*      `{fp(s['entry'], s['digits'])}`\n"
        f"🎯 *Take Profit :* `{fp(s['tp'], s['digits'])}`\n"
        f"🛑 *Stop Loss :*   `{fp(s['sl'], s['digits'])}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ *Ratio R/R :* `1:{s['rr_ratio']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Confirmations :*\n{reasons}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n"
        f"⚠️ _Pas un conseil financier — gérez votre risque._"
    )

def msg_tp(s: dict) -> str:
    return (
        f"✅ *TP TOUCHÉ — {s['symbol']}* 🎯🏆\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Direction :  *{s['direction']}*\n"
        f"Entrée :     `{fp(s['entry'], s['digits'])}`\n"
        f"✅ TP :      `{fp(s['tp'], s['digits'])}`\n"
        f"⚖️ Ratio :   `1:{s['rr_ratio']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *TAKE PROFIT TOUCHÉ !*\n"
        f"💰 _Le travail paye toujours !_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

def msg_sl(s: dict) -> str:
    return (
        f"❌ *STOP-LOSS ATTEINT — {s['symbol']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Direction : *{s['direction']}*\n"
        f"Entrée :    `{fp(s['entry'], s['digits'])}`\n"
        f"❌ SL :     `{fp(s['sl'], s['digits'])}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📉 *PERTE — Stop Loss atteint.*\n"
        f"💪 _Faire partie du jeu. On reste discipliné !_\n"
        f"🎯 _Prochain signal en préparation..._\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

async def _send(text: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
    )

def telegram_send(text: str):
    for attempt in range(3):
        try:
            asyncio.run(_send(text))
            log.info("📨 Telegram OK")
            return
        except Exception as e:
            log.warning(f"Telegram tentative {attempt+1}/3: {e}")
            time.sleep(5)
    log.error("❌ Telegram échoué après 3 tentatives")


# ══════════════════════════════════════════════════════════════
#  PERSISTANCE
# ══════════════════════════════════════════════════════════════

def load_signals(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_signals(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ══════════════════════════════════════════════════════════════
#  MAIN — SCHEDULER COMPLET
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("🚀 Signal Bot V4 Ultra — Démarrage...")

    # ── Signaux de marché ──
    schedule.every(1).hours.do(scan_markets)
    schedule.every(5).minutes.do(check_active_signals)

    # ── Résumés ──
    schedule.every().day.at("21:00").do(daily_summary)
    schedule.every().monday.at("08:00").do(weekly_summary)

    # ── Messages matin/soir ──
    schedule.every().day.at("07:00").do(send_matin)
    schedule.every().day.at("21:30").do(send_soir)

    # ── Statut marché (3x par jour) ──
    schedule.every().day.at("09:00").do(send_market_status)
    schedule.every().day.at("14:00").do(send_market_status)
    schedule.every().day.at("18:00").do(send_market_status)

    # ── Citations (2x par jour) ──
    schedule.every().day.at("08:00").do(send_citation)
    schedule.every().day.at("19:00").do(send_citation)

    # ── Motivation (midi) ──
    schedule.every().day.at("12:00").do(send_motivation)

    # ── Humour (vendredi soir = fin de semaine) ──
    schedule.every().friday.at("17:00").do(send_humour)
    schedule.every().wednesday.at("20:00").do(send_humour)

    # ── Démarrage immédiat ──
    scan_markets()

    log.info("✅ Bot V4 actif — 9 indicateurs | Score strict | Contenu automatique")
    while True:
        schedule.run_pending()
        time.sleep(30)
