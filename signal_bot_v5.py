"""
╔══════════════════════════════════════════════════════════════╗
║           SIGNAL BOT V5 — SNIPER EDITION                    ║
║  SMC | Liquidité | Multi-TP | Réponse Message | News        ║
║  Twelve Data | Railway | Telegram                           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, time, json, random, asyncio, logging, requests
import pandas as pd
import numpy as np
import schedule
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "VOTRE_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@VOTRE_CANAL")
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY",   "VOTRE_CLE")

SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "GBP/JPY", "EUR/JPY",
    "XAU/USD", "XAG/USD",
    "BTC/USD", "ETH/USD",
]

MIN_SCORE          = 60    # Score minimum strict
MIN_RR             = 1.5   # Ratio R/R minimum
MAX_ACTIFS         = 3     # Signaux actifs simultanés max
MIN_ADX            = 18    # Force tendance minimale

SIGNALS_FILE = "signals.json"
HISTORY_FILE = "history.json"

# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_v5.log", encoding="utf-8"),
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
    "💬 _\"Votre plan de trading est votre meilleur ami.\"_\n— Alexander Elder",
    "💬 _\"Les marchés sont guidés par la peur et la cupidité.\"_\n— Warren Buffett",
    "💬 _\"Le trading est simple, mais pas facile.\"_\n— Ed Seykota",
]

HUMOUR = [
    "😂 *Moi avant le trade :* \"Je vais juste regarder le marché...\"\n*Moi 3h après :* 📉💸😭",
    "🤡 *Le marché quand j'achète :* descend\n*Le marché quand je vends :* monte\n\nLogique non ? 😭",
    "😅 *Stop Loss touché à -15 pips*\nLe marché 5 min après : 📈+200 pips\n\n_\"Bien sûr...\"_ 😑",
    "🧘 *Technique de méditation du trader :*\nFerme les yeux → Respire → Ne regarde PAS le graphique → Répète 😂",
    "💀 *Mon portefeuille après avoir ignoré le Stop Loss :*\n📉📉📉📉📉\n\n*Leçon : TOUJOURS mettre le SL* ✅",
    "🤓 *J'ai analysé 6h, utilisé 12 indicateurs, regardé 5 timeframes...*\n\nLe marché : fait exactement l'inverse 😭",
    "💪 *Un trader perdant est juste un trader gagnant qui n'a pas encore arrêté.*\nContinuez ! 🔥",
    "🎰 *La différence entre le trading et le casino ?*\nAu casino ils te donnent des boissons gratuites 😂",
]

MOTIVATION = [
    "🔥 *La patience est la clé.* Pas de signal = pas de perte. On attend le setup parfait !",
    "💪 *Rappel :* Ne forcez jamais un trade. Le marché sera là demain.",
    "🧠 *Mindset :* Les pros ne cherchent pas à tout trader — ils cherchent LES bons trades.",
    "⚡ *Discipline > Émotion.* Suivez le plan, ignorez le bruit.",
    "🎯 *Qualité > Quantité.* 3 bons signaux valent mieux que 20 mauvais.",
    "🛡️ *Protégez votre capital d'abord.* Les profits viennent ensuite.",
    "📈 *Le trend est votre ami.* Ne tradez jamais contre la tendance principale.",
]

MATIN = [
    "🌅 *BONJOUR TRADERS !*\n\nNouvelle session, nouvelles opportunités !\n📊 Le bot analyse en continu.\n💪 Bonne session à tous !",
    "☀️ *RÉVEIL DU TRADER !*\n\nLa session de Londres approche !\nC'est souvent là que les meilleurs setups apparaissent.\n🎯 On reste focus ! Let's go !",
    "🔔 *SESSION EUROPÉENNE BIENTÔT !*\n\nTop paires à surveiller :\n→ XAU/USD 👀\n→ EUR/USD 👀\n→ GBP/USD 👀\n\nLe bot analyse en continu 🤖",
]

SOIR = [
    "🌙 *FIN DE SESSION !*\n\nLa session américaine se termine.\n💤 Le bot continue de surveiller.\nBonne nuit traders ! 😴",
    "🌆 *BILAN DE SOIRÉE*\n\nConsultez le résumé quotidien ci-dessous.\n🙏 Merci d'être avec nous !\nOn se retrouve demain 💪",
]

# ══════════════════════════════════════════════════════════════
#  TWELVE DATA
# ══════════════════════════════════════════════════════════════

BASE = "https://api.twelvedata.com"

def fetch_ohlcv(symbol: str, interval: str, bars: int = 200) -> Optional[pd.DataFrame]:
    try:
        r = requests.get(f"{BASE}/time_series", params={
            "symbol": symbol, "interval": interval,
            "outputsize": bars, "apikey": TWELVEDATA_KEY
        }, timeout=15)
        d = r.json()
        if d.get("status") == "error":
            return None
        vals = d.get("values", [])
        if not vals:
            return None
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
    if "JPY" in symbol: return 3
    if "BTC" in symbol: return 2
    if "ETH" in symbol: return 2
    if "XAU" in symbol: return 2
    if "XAG" in symbol: return 3
    return 5

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
    sig = m.ewm(span=9,adjust=False).mean()
    return m, sig

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
    lo  = rsi.rolling(p).min()
    hi  = rsi.rolling(p).max()
    return 100*(rsi-lo)/(hi-lo+1e-10)

def calc_wr(df: pd.DataFrame, p=14) -> pd.Series:
    hi = df["high"].rolling(p).max()
    lo = df["low"].rolling(p).min()
    return -100*(hi-df["close"])/(hi-lo+1e-10)

# ══════════════════════════════════════════════════════════════
#  CONCEPTS SMC — SMART MONEY
# ══════════════════════════════════════════════════════════════

def detect_order_blocks(df: pd.DataFrame, direction: str, lookback=30) -> Optional[dict]:
    """
    Détecte le dernier Order Block valide.
    BUY  → dernier down candle avant une impulsion haussière
    SELL → dernier up candle avant une impulsion baissière
    """
    try:
        recent = df.tail(lookback).copy()
        recent["body"] = recent["close"] - recent["open"]

        if direction == "BUY":
            # Cherche dernière bougie baissière suivie d'une forte hausse
            for i in range(len(recent)-3, 0, -1):
                if recent["body"].iloc[i] < 0:  # bougie baissière
                    # Vérifier impulsion haussière après
                    if recent["close"].iloc[i+1] > recent["high"].iloc[i]:
                        ob = {
                            "high": float(recent["high"].iloc[i]),
                            "low":  float(recent["low"].iloc[i]),
                            "mid":  float((recent["high"].iloc[i] + recent["low"].iloc[i])/2)
                        }
                        return ob
        else:
            for i in range(len(recent)-3, 0, -1):
                if recent["body"].iloc[i] > 0:  # bougie haussière
                    if recent["close"].iloc[i+1] < recent["low"].iloc[i]:
                        ob = {
                            "high": float(recent["high"].iloc[i]),
                            "low":  float(recent["low"].iloc[i]),
                            "mid":  float((recent["high"].iloc[i] + recent["low"].iloc[i])/2)
                        }
                        return ob
        return None
    except:
        return None

def detect_fvg(df: pd.DataFrame, direction: str) -> bool:
    """
    Fair Value Gap — gap entre bougie N-2 et N.
    BUY  → low[N] > high[N-2] (gap haussier)
    SELL → high[N] < low[N-2] (gap baissier)
    """
    try:
        c = df.tail(5)
        for i in range(2, len(c)):
            if direction == "BUY":
                if c["low"].iloc[i] > c["high"].iloc[i-2]:
                    return True
            else:
                if c["high"].iloc[i] < c["low"].iloc[i-2]:
                    return True
        return False
    except:
        return False

def detect_liquidity_zones(df: pd.DataFrame, window=20) -> dict:
    """
    Zones de liquidité = niveaux où le prix a réagi plusieurs fois.
    Equal highs/lows = liquidité au-dessus/en-dessous.
    """
    try:
        recent = df.tail(window)
        highs  = recent["high"].values
        lows   = recent["low"].values

        # Equal highs (liquidité sell-side au-dessus)
        eq_high_level = None
        for i in range(len(highs)-1):
            for j in range(i+1, len(highs)):
                if abs(highs[i] - highs[j]) / highs[i] < 0.001:  # 0.1% tolérance
                    eq_high_level = max(highs[i], highs[j])
                    break

        # Equal lows (liquidité buy-side en-dessous)
        eq_low_level = None
        for i in range(len(lows)-1):
            for j in range(i+1, len(lows)):
                if abs(lows[i] - lows[j]) / lows[i] < 0.001:
                    eq_low_level = min(lows[i], lows[j])
                    break

        return {
            "buy_liquidity":  eq_low_level,   # Zone de liquidité en-dessous
            "sell_liquidity": eq_high_level,   # Zone de liquidité au-dessus
            "resistance":     float(recent["high"].max()),
            "support":        float(recent["low"].min()),
        }
    except:
        return {"buy_liquidity": None, "sell_liquidity": None,
                "resistance": 0, "support": 0}

def detect_sweep(df: pd.DataFrame, direction: str, liq: dict) -> bool:
    """
    Confirmation de sweep LÉGÈRE — 1 bougie suffit.

    BUY sweep :
      - Le prix est descendu SOUS les equal lows (low[i] < buy_liquidity)
      - La bougie suivante CLÔTURE au-dessus (close[i+1] > buy_liquidity)
      → Sweep confirmé → signal BUY valide

    SELL sweep :
      - Le prix est monté AU-DESSUS des equal highs (high[i] > sell_liquidity)
      - La bougie suivante CLÔTURE en-dessous (close[i+1] < sell_liquidity)
      → Sweep confirmé → signal SELL valide

    Si pas de zone de liquidité détectée → on laisse passer (pas de blocage)
    """
    try:
        recent = df.tail(6)

        if direction == "BUY":
            level = liq.get("buy_liquidity")
            if not level:
                return True  # Pas de zone détectée → on ne bloque pas
            for i in range(len(recent)-2):
                swept  = recent["low"].iloc[i] < level
                closed = recent["close"].iloc[i+1] > level
                if swept and closed:
                    return True
            # Vérif bougie actuelle aussi
            if recent["low"].iloc[-2] < level and recent["close"].iloc[-1] > level:
                return True
            return False

        else:  # SELL
            level = liq.get("sell_liquidity")
            if not level:
                return True
            for i in range(len(recent)-2):
                swept  = recent["high"].iloc[i] > level
                closed = recent["close"].iloc[i+1] < level
                if swept and closed:
                    return True
            if recent["high"].iloc[-2] > level and recent["close"].iloc[-1] < level:
                return True
            return False

    except Exception as e:
        log.warning(f"detect_sweep error: {e}")
        return True  # En cas d'erreur on ne bloque pas

def market_structure(df: pd.DataFrame) -> str:
    """
    Détection de la structure de marché.
    HH+HL = Bullish | LH+LL = Bearish | Sinon = Ranging
    """
    try:
        c = df["close"].tail(20).values
        highs = []
        lows  = []
        for i in range(1, len(c)-1):
            if c[i] > c[i-1] and c[i] > c[i+1]: highs.append(c[i])
            if c[i] < c[i-1] and c[i] < c[i+1]: lows.append(c[i])

        if len(highs) >= 2 and len(lows) >= 2:
            hh = highs[-1] > highs[-2]
            hl = lows[-1]  > lows[-2]
            lh = highs[-1] < highs[-2]
            ll = lows[-1]  < lows[-2]
            if hh and hl: return "BULLISH"
            if lh and ll: return "BEARISH"
        return "RANGING"
    except:
        return "RANGING"

def premium_discount_zone(df: pd.DataFrame, price: float) -> str:
    """
    Premium = prix dans la moitié haute du range (vendre)
    Discount = prix dans la moitié basse du range (acheter)
    """
    try:
        hi = df["high"].tail(50).max()
        lo = df["low"].tail(50).min()
        mid = (hi + lo) / 2
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
    if len(df) < 60: return None
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
            "srsi":    float(srsi.iloc[-1]),
            "wr":      float(wr.iloc[-1]),
            "close":   float(c.iloc[-1]),
            "atr":     float(calc_atr(df).iloc[-1]),
        }
    except Exception as e:
        log.error(f"analyze_tf: {e}")
        return None

# ══════════════════════════════════════════════════════════════
#  SCORE DE CONFLUENCE
# ══════════════════════════════════════════════════════════════

def compute_confluence(fast, med, slow, direction: str, smc: dict) -> Tuple[int, list]:
    score = 0
    confirmations = []
    buy = direction == "BUY"

    # RSI (12 pts)
    if fast["rsi"] < 38 if buy else fast["rsi"] > 62:
        score += 4
        confirmations.append(f"📊 RSI M15 {'survendu' if buy else 'suracheté'} ({fast['rsi']:.0f})")
    if med["rsi"] < 52 if buy else med["rsi"] > 48:
        score += 4
        confirmations.append(f"📊 RSI H1 ({med['rsi']:.0f})")
    if slow["rsi"] < 55 if buy else slow["rsi"] > 45:
        score += 4

    # StochRSI (8 pts)
    if fast["srsi"] < 25 if buy else fast["srsi"] > 75:
        score += 8
        confirmations.append(f"⚡ StochRSI {'survendu' if buy else 'suracheté'} ({fast['srsi']:.0f})")

    # Williams %R (6 pts)
    if fast["wr"] < -75 if buy else fast["wr"] > -25:
        score += 6
        confirmations.append(f"📉 W%R {fast['wr']:.1f}")

    # MACD croisement (12 pts)
    cross = (fast["macd"] > fast["macd_s"] and fast["macd_p"] <= fast["ms_p"]) if buy \
       else (fast["macd"] < fast["macd_s"] and fast["macd_p"] >= fast["ms_p"])
    if cross:
        score += 6
        confirmations.append(f"🔀 MACD M15 croise {'↑' if buy else '↓'}")
    if (med["macd"] > med["macd_s"]) if buy else (med["macd"] < med["macd_s"]):
        score += 4
    if (slow["macd"] > slow["macd_s"]) if buy else (slow["macd"] < slow["macd_s"]):
        score += 2

    # EMA (12 pts)
    if (med["ema20"] > med["ema50"]) if buy else (med["ema20"] < med["ema50"]):
        score += 6
        confirmations.append(f"📈 EMA20 {'>' if buy else '<'} EMA50 H1")
    if (slow["ema20"] > slow["ema200"]) if buy else (slow["ema20"] < slow["ema200"]):
        score += 6
        confirmations.append("📈 Tendance H4 alignée")

    # Bollinger (8 pts)
    if (fast["close"] < fast["bb_l"]) if buy else (fast["close"] > fast["bb_u"]):
        score += 8
        confirmations.append(f"🎯 Prix {'sous BB bas' if buy else 'au-dessus BB haut'}")

    # Stochastique (6 pts)
    stok = (fast["stoch_k"] < 25 and fast["stoch_k"] > fast["stoch_d"]) if buy \
      else (fast["stoch_k"] > 75 and fast["stoch_k"] < fast["stoch_d"])
    if stok:
        score += 6
        confirmations.append(f"🔄 Stoch croise {'↑' if buy else '↓'}")

    # ADX (8 pts)
    if med["adx"] > MIN_ADX:
        score += 4
        confirmations.append(f"💪 ADX={med['adx']:.0f} fort")
    if (med["pdi"] > med["ndi"]) if buy else (med["ndi"] > med["pdi"]):
        score += 4

    # SMC — Order Block (10 pts)
    if smc.get("order_block"):
        score += 10
        confirmations.append(f"🧱 Order Block détecté")

    # SMC — Fair Value Gap (8 pts)
    if smc.get("fvg"):
        score += 8
        confirmations.append("🌐 Fair Value Gap présent")

    # SMC — Structure (6 pts)
    struct = smc.get("structure","")
    if (struct == "BULLISH") if buy else (struct == "BEARISH"):
        score += 6
        confirmations.append(f"🏗️ Structure {'haussière' if buy else 'baissière'}")

    # Liquidité (4 pts)
    liq = smc.get("liquidity", {})
    if buy and liq.get("buy_liquidity"):
        score += 4
        confirmations.append("💧 Zone liquidité BUY")
    elif not buy and liq.get("sell_liquidity"):
        score += 4
        confirmations.append("💧 Zone liquidité SELL")

    return min(int(score), 100), confirmations[:6]

# ══════════════════════════════════════════════════════════════
#  MULTI-TP DYNAMIQUES
# ══════════════════════════════════════════════════════════════

def compute_multi_tp(entry: float, sl: float, direction: str,
                     atr: float, score: int, digits: int) -> List[dict]:
    """
    Calcule 2 à 4 TP selon le score de confluence et la volatilité.
    Score >= 80 → 4 TP | Score >= 70 → 3 TP | Score >= 60 → 2 TP
    """
    sl_dist = abs(entry - sl)
    tps = []

    if score >= 80:
        ratios = [1.0, 1.5, 2.5, 4.0]
    elif score >= 70:
        ratios = [1.0, 1.8, 3.0]
    else:
        ratios = [1.0, 2.0]

    for i, ratio in enumerate(ratios):
        dist = sl_dist * ratio
        if direction == "BUY":
            tp_price = entry + dist
        else:
            tp_price = entry - dist
        tps.append({
            "level": i+1,
            "price": round(tp_price, digits),
            "ratio": ratio,
            "hit":   False,
        })

    return tps

# ══════════════════════════════════════════════════════════════
#  FILTRE NEWS
# ══════════════════════════════════════════════════════════════

def is_news_blackout(symbol: str) -> Tuple[bool, str]:
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return True, "Week-end"
    if now.weekday() == 4 and 12 <= now.hour <= 13:
        return True, "NFP vendredi"
    if now.weekday() == 2 and 18 <= now.hour <= 19:
        return True, "FOMC mercredi"
    if now.weekday() == 1 and 14 <= now.hour <= 15:
        return True, "RBA mardi"
    if now.weekday() == 3 and 11 <= now.hour <= 12:
        return True, "BCE jeudi"
    return False, ""

def get_session() -> str:
    h = datetime.now(timezone.utc).hour
    if 7 <= h < 16:  return "🇪🇺 Session Européenne"
    if 12 <= h < 21: return "🇺🇸 Session Américaine"
    if 0 <= h < 9:   return "🇯🇵 Session Asiatique"
    return "😴 Marché calme"

# ══════════════════════════════════════════════════════════════
#  ANALYSE COMPLÈTE
# ══════════════════════════════════════════════════════════════

def analyze_symbol(symbol: str) -> Optional[dict]:
    # Fetch 3 timeframes
    df15 = fetch_ohlcv(symbol, "15min", 150); time.sleep(0.8)
    df1h = fetch_ohlcv(symbol, "1h",   250);  time.sleep(0.8)
    df4h = fetch_ohlcv(symbol, "4h",   150);  time.sleep(0.8)

    if df15 is None or df1h is None or df4h is None:
        return None

    fast = analyze_tf(df15)
    med  = analyze_tf(df1h)
    slow = analyze_tf(df4h)
    if not fast or not med or not slow:
        return None

    # Direction consensus
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

    if buy_pts >= 4:   direction = "BUY"
    elif sell_pts >= 4: direction = "SELL"
    else: return None

    # SMC Analysis
    struct = market_structure(df1h)
    ob     = detect_order_blocks(df1h, direction)
    fvg    = detect_fvg(df15, direction)
    liq    = detect_liquidity_zones(df1h)

    smc = {
        "order_block": ob,
        "fvg":         fvg,
        "structure":   struct,
        "liquidity":   liq,
    }

    # Score
    score, confirmations = compute_confluence(fast, med, slow, direction, smc)

    if score < MIN_SCORE:
        log.info(f"{symbol}: score {score}/100 < {MIN_SCORE} — refusé")
        return None

    # ── SWEEP — bonus score au lieu de blocage ──
    sweep_ok = detect_sweep(df15, direction, liq)
    if sweep_ok:
        score = min(score + 15, 100)
        confirmations.append("💧 Sweep liquidité confirmé ✅")
        log.info(f"{symbol}: ✅ sweep confirmé → score boosté à {score}/100")
    else:
        # Entrée prématurée — score réduit de 10 pts
        score = max(score - 10, 0)
        confirmations.append("⚠️ Entrée avant sweep — risque accru")
        log.info(f"{symbol}: ⚠️ sweep non confirmé → score réduit à {score}/100")

        # Re-vérifier le score minimum après réduction
        if score < MIN_SCORE:
            log.info(f"{symbol}: score {score}/100 trop bas après réduction — refusé")
            return None

    # Prix
    price = fetch_price(symbol); time.sleep(0.5)
    if not price: price = med["close"]

    # SL intelligent — placé AU-DESSUS des zones de liquidité
    atr_val = med["atr"]
    buffer  = atr_val * 0.2  # petit buffer au-delà de la zone

    if direction == "BUY":
        # Priorité : en-dessous de la zone de liquidité buy (equal lows)
        if liq.get("buy_liquidity"):
            sl = liq["buy_liquidity"] - buffer
            log.info(f"{symbol}: SL sous liquidité buy @ {sl:.5f}")
        elif ob:
            sl = ob["low"] - buffer
            log.info(f"{symbol}: SL sous Order Block @ {sl:.5f}")
        else:
            sl = price - atr_val * 1.2
    else:
        # Priorité : au-dessus de la zone de liquidité sell (equal highs)
        if liq.get("sell_liquidity"):
            sl = liq["sell_liquidity"] + buffer
            log.info(f"{symbol}: SL au-dessus liquidité sell @ {sl:.5f}")
        elif ob:
            sl = ob["high"] + buffer
            log.info(f"{symbol}: SL au-dessus Order Block @ {sl:.5f}")
        else:
            sl = price + atr_val * 1.2

    # Vérification distance SL minimum
    sl_dist = abs(price - sl)
    if sl_dist < atr_val * 0.5:
        sl_dist = atr_val * 1.0
        sl = price - sl_dist if direction == "BUY" else price + sl_dist

    # Filtre news
    blackout, reason = is_news_blackout(symbol)
    if blackout:
        log.info(f"{symbol}: blackout news ({reason})")
        return None

    digits = get_digits(symbol)
    clean  = symbol.replace("/", "")

    # Multi TP
    tps = compute_multi_tp(price, sl, direction, atr_val, score, digits)

    # Zone premium/discount
    zone = premium_discount_zone(df1h, price)

    # Volatilité
    atr_pct = (atr_val / price) * 100
    volatility = "🔥 HAUTE" if atr_pct > 0.5 else "📊 NORMALE" if atr_pct > 0.2 else "😴 BASSE"

    return {
        "symbol":        clean,
        "direction":     direction,
        "entry":         round(price, digits),
        "sl":            round(sl, digits),
        "tps":           tps,
        "score":         score,
        "confirmations": confirmations,
        "structure":     struct,
        "zone":          zone,
        "volatility":    volatility,
        "fvg":           fvg,
        "ob":            ob is not None,
        "sweep":         sweep_ok,
        "rsi_h1":        round(med["rsi"], 1),
        "srsi":          round(fast["srsi"], 1),
        "wr":            round(fast["wr"], 1),
        "adx":           round(med["adx"], 1),
        "atr":           round(atr_val, digits),
        "digits":        digits,
        "session":       get_session(),
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "message_id":    None,   # ID du message Telegram pour répondre
        "closed":        False,
        "result":        None,
    }

# ══════════════════════════════════════════════════════════════
#  MESSAGES TELEGRAM
# ══════════════════════════════════════════════════════════════

def fp(val: float, digits: int) -> str:
    return f"{val:.{digits}f}"

def confluence_bar(score: int) -> str:
    filled = round(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"`{bar}` {score}%"

def nb_tps(tps: list) -> int:
    return len(tps)

def build_signal_msg(s: dict) -> str:
    emoji  = "🟢" if s["direction"] == "BUY" else "🔴"
    action = "BUY" if s["direction"] == "BUY" else "SELL"
    arrow  = "📈" if s["direction"] == "BUY" else "📉"

    # TPs
    tp_lines = ""
    for tp in s["tps"]:
        tp_lines += f"  ├─TP{tp['level']} `{fp(tp['price'], s['digits'])}` — R:R {tp['ratio']}x ─{'─'*int(tp['ratio'])}\n"

    # Confirmations
    conf_text = "\n".join([f"  {c}" for c in s["confirmations"]])

    return (
        f"{'═'*26}\n"
        f"{emoji} *{s['symbol']} SNIPER — {action}* {arrow}\n"
        f"{'═'*26}\n\n"
        f"🎯 *ENTRÉE :* `{fp(s['entry'], s['digits'])}`\n"
        f"🛑 *STOP LOSS :* `{fp(s['sl'], s['digits'])}`\n\n"
        f"🏹 *TAKE PROFITS ({nb_tps(s['tps'])} TP)*\n"
        f"{tp_lines}\n"
        f"{'─'*26}\n"
        f"🧠 *CONFLUENCE* {confluence_bar(s['score'])}\n"
        f"  📊 RSI `{s['rsi_h1']}` | ⚡ StochRSI `{s['srsi']}` | 📉 W%R `{s['wr']}`\n"
        f"  💨 Volatilité : {s['volatility']} — {nb_tps(s['tps'])} TP\n"
        f"  ⚠️ Zone : {s['zone']}\n"
        f"  🏗️ Structure : {s['structure']}\n"
        f"  💧 Sweep : {'✅ Confirmé — entrée optimale' if s.get('sweep') else '⚠️ Avant sweep — SL plus large conseillé'}\n"
        f"{'─'*26}\n"
        f"{conf_text}\n"
        f"{'─'*26}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n"
        f"{s['session']}\n"
        f"{'═'*26}\n"
        f"⚠️ _Gérez votre risque._"
    )

def build_tp_msg(s: dict, tp: dict) -> str:
    is_last = tp["level"] == nb_tps(s["tps"])
    emoji = "🏆" if is_last else "✅"
    return (
        f"{emoji} *TP{tp['level']} TOUCHÉ — {s['symbol']}*\n"
        f"{'─'*24}\n"
        f"Direction : *{s['direction']}*\n"
        f"Entrée :    `{fp(s['entry'], s['digits'])}`\n"
        f"✅ TP{tp['level']} :  `{fp(tp['price'], s['digits'])}` (R:R {tp['ratio']}x)\n"
        f"{'─'*24}\n"
        f"{'🏆 *DERNIER TP TOUCHÉ !* 🎉' if is_last else '💰 *Partiels sécurisés !*'}\n"
        f"{'💪 Excellent résultat !' if is_last else '🔒 Déplacez le SL à l entrée.'}\n"
        f"{'─'*24}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

def build_sl_msg(s: dict) -> str:
    tps_hit = [t for t in s["tps"] if t.get("hit")]
    partial = f"\n✅ TP partiels touchés : {len(tps_hit)}/{nb_tps(s['tps'])}" if tps_hit else ""
    return (
        f"❌ *STOP-LOSS ATTEINT — {s['symbol']}*\n"
        f"{'─'*24}\n"
        f"Direction : *{s['direction']}*\n"
        f"Entrée :    `{fp(s['entry'], s['digits'])}`\n"
        f"❌ SL :     `{fp(s['sl'], s['digits'])}`\n"
        f"{partial}\n"
        f"{'─'*24}\n"
        f"📉 *PERTE — Stop Loss atteint.*\n"
        f"💪 _Faire partie du jeu. On reste discipliné !_\n"
        f"🎯 _Prochain signal en préparation..._\n"
        f"{'─'*24}\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC"
    )

# ══════════════════════════════════════════════════════════════
#  TELEGRAM — ENVOI + RÉPONSE AU MESSAGE ORIGINAL
# ══════════════════════════════════════════════════════════════

async def _send(text: str, reply_to: int = None) -> Optional[int]:
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=reply_to,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
    )
    return msg.message_id

def telegram_send(text: str, reply_to: int = None) -> Optional[int]:
    for attempt in range(3):
        try:
            msg_id = asyncio.run(_send(text, reply_to))
            log.info("📨 Telegram OK")
            return msg_id
        except Exception as e:
            log.warning(f"Telegram tentative {attempt+1}/3: {e}")
            time.sleep(5)
    log.error("❌ Telegram échoué")
    return None

# ══════════════════════════════════════════════════════════════
#  SURVEILLANCE TP/SL
# ══════════════════════════════════════════════════════════════

def check_active_signals():
    signals = load(SIGNALS_FILE)
    if not signals: return

    updated = False
    for key, s in list(signals.items()):
        if s.get("closed"): continue

        raw = s["symbol"]
        sym = raw[:3] + "/" + raw[3:]
        price = fetch_price(sym); time.sleep(0.8)
        if not price: continue

        msg_id = s.get("message_id")

        # Vérif TPs dans l'ordre
        all_hit = True
        for tp in s["tps"]:
            if tp.get("hit"): continue
            all_hit = False

            tp_hit = (price >= tp["price"]) if s["direction"] == "BUY" \
                else (price <= tp["price"])

            if tp_hit:
                tp["hit"] = True
                updated = True
                log.info(f"[{s['symbol']}] ✅ TP{tp['level']} @ {price}")
                telegram_send(build_tp_msg(s, tp), reply_to=msg_id)
                break  # Un TP à la fois

        # Vérif SL
        sl_hit = (price <= s["sl"]) if s["direction"] == "BUY" \
            else (price >= s["sl"])

        if sl_hit:
            s["closed"]     = True
            s["result"]     = "SL"
            s["close_time"] = datetime.now(timezone.utc).isoformat()
            updated = True
            log.info(f"[{s['symbol']}] ❌ SL @ {price}")
            telegram_send(build_sl_msg(s), reply_to=msg_id)

            history = load(HISTORY_FILE)
            history[key] = s
            save(HISTORY_FILE, history)
            continue

        # Tous les TPs touchés → signal fermé
        if all([t.get("hit") for t in s["tps"]]):
            s["closed"]     = True
            s["result"]     = "TP"
            s["close_time"] = datetime.now(timezone.utc).isoformat()
            updated = True
            history = load(HISTORY_FILE)
            history[key] = s
            save(HISTORY_FILE, history)

    if updated:
        save(SIGNALS_FILE, signals)

# ══════════════════════════════════════════════════════════════
#  SCAN DES MARCHÉS
# ══════════════════════════════════════════════════════════════

def scan_markets():
    log.info("🔍 Scan Sniper Edition — SMC + Confluence...")
    signals = load(SIGNALS_FILE)

    actifs = [s for s in signals.values() if not s.get("closed")]
    if len(actifs) >= MAX_ACTIFS:
        log.info(f"Max {MAX_ACTIFS} signaux actifs")
        return

    for symbol in SYMBOLS:
        clean = symbol.replace("/","")
        if any(s["symbol"]==clean and not s.get("closed") for s in signals.values()):
            continue

        result = analyze_symbol(symbol)
        if result:
            log.info(f"✅ {result['symbol']} {result['direction']} | Score: {result['score']}/100 | TPs: {nb_tps(result['tps'])}")
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
#  RÉSUMÉS
# ══════════════════════════════════════════════════════════════

def daily_summary():
    history = load(HISTORY_FILE)
    today   = datetime.now(timezone.utc).date()
    tp_count = sl_count = total = 0
    lines = []

    for s in history.values():
        try:
            if datetime.fromisoformat(s.get("close_time","")).date() != today: continue
        except: continue
        total += 1
        if s.get("result") == "TP":
            tp_count += 1
            tps_hit = sum(1 for t in s.get("tps",[]) if t.get("hit"))
            lines.append(f"✅ {s['symbol']} {s['direction']} ({tps_hit} TP touchés)")
        else:
            tps_hit = sum(1 for t in s.get("tps",[]) if t.get("hit"))
            sl_count += 1
            lines.append(f"❌ {s['symbol']} {s['direction']}" + (f" ({tps_hit} partiels)" if tps_hit else ""))

    if total == 0: return
    winrate = tp_count/total*100
    stars = "⭐"*min(int(winrate/20),5)
    perf = "🏆 EXCELLENTE" if winrate>=70 else "💪 BONNE" if winrate>=55 else "📊 CORRECTE"

    msg = (
        f"📊 *RÉSUMÉ DU JOUR — {today.strftime('%d/%m/%Y')}*\n"
        f"{'─'*24}\n"
        f"✅ TP touchés :   *{tp_count}*\n"
        f"❌ SL atteints :  *{sl_count}*\n"
        f"📈 Total :        *{total}*\n"
        f"🎯 Winrate :      *{winrate:.0f}%* {stars}\n"
        f"{'─'*24}\n"
        f"Performance : {perf} SESSION\n"
        f"{'─'*24}\n"
        f"{chr(10).join(lines)}\n"
        f"{'─'*24}\n"
        f"🤖 _Sniper Bot V5 — SMC | Multi-TP | 11 indicateurs_"
    )
    telegram_send(msg)

def weekly_summary():
    history  = load(HISTORY_FILE)
    today    = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    tp = sl = 0
    best = {}

    for s in history.values():
        try: d = datetime.fromisoformat(s.get("close_time","")).date()
        except: continue
        if not (week_ago <= d <= today): continue
        sym = s["symbol"]
        if sym not in best: best[sym] = {"tp":0,"sl":0}
        if s.get("result")=="TP": tp+=1; best[sym]["tp"]+=1
        else: sl+=1; best[sym]["sl"]+=1

    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))

    msg = (
        f"📅 *BILAN HEBDOMADAIRE*\n"
        f"{'─'*24}\n"
        f"📆 {week_ago.strftime('%d/%m')} → {today.strftime('%d/%m/%Y')}\n\n"
        f"✅ TP : *{tp}* | ❌ SL : *{sl}*\n"
        f"🎯 Winrate : *{wr:.0f}%*\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"{'─'*24}\n"
        f"{'🔥 Semaine exceptionnelle !' if wr>=70 else '💪 Continuons !' if wr>=50 else '📚 On progresse !'}\n"
        f"_Nouvelle semaine, nouvelles opportunités !_ 🚀"
    )
    telegram_send(msg)

def monthly_summary():
    history    = load(HISTORY_FILE)
    today      = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    tp = sl = 0
    best = {}
    total_tps_hit = 0

    for s in history.values():
        try: d = datetime.fromisoformat(s.get("close_time","")).date()
        except: continue
        if not (month_start <= d <= today): continue
        sym = s["symbol"]
        if sym not in best: best[sym] = {"tp":0,"sl":0}
        tps_hit = sum(1 for t in s.get("tps",[]) if t.get("hit"))
        total_tps_hit += tps_hit
        if s.get("result")=="TP": tp+=1; best[sym]["tp"]+=1
        else: sl+=1; best[sym]["sl"]+=1

    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    stars = "⭐"*min(int(wr/20),5)
    mois = today.strftime("%B %Y")

    msg = (
        f"📆 *BILAN MENSUEL — {mois.upper()}*\n"
        f"{'═'*24}\n"
        f"✅ Signaux TP :    *{tp}*\n"
        f"❌ Signaux SL :    *{sl}*\n"
        f"🏹 TP niveaux touchés : *{total_tps_hit}*\n"
        f"📈 Total signaux : *{total}*\n"
        f"🎯 Winrate :       *{wr:.0f}%* {stars}\n"
        f"{'─'*24}\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"{'─'*24}\n"
        f"{'🔥 MOIS EXCEPTIONNEL !' if wr>=70 else '💪 Bon mois !' if wr>=55 else '📚 On progresse chaque mois !'}\n"
        f"{'═'*24}\n"
        f"_Merci pour votre confiance ce mois-ci !_ 🙏\n"
        f"_Le prochain mois sera encore meilleur._ 🚀"
    )
    telegram_send(msg)

def yearly_summary():
    history     = load(HISTORY_FILE)
    today       = datetime.now(timezone.utc).date()
    year_start  = today.replace(month=1, day=1)
    tp = sl = 0
    best = {}
    monthly_stats = {}
    total_tps_hit = 0

    for s in history.values():
        try: d = datetime.fromisoformat(s.get("close_time","")).date()
        except: continue
        if d.year != today.year: continue

        sym = s["symbol"]
        month_key = d.strftime("%B")
        if sym not in best: best[sym] = {"tp":0,"sl":0}
        if month_key not in monthly_stats: monthly_stats[month_key] = {"tp":0,"sl":0}

        tps_hit = sum(1 for t in s.get("tps",[]) if t.get("hit"))
        total_tps_hit += tps_hit

        if s.get("result")=="TP":
            tp+=1; best[sym]["tp"]+=1; monthly_stats[month_key]["tp"]+=1
        else:
            sl+=1; best[sym]["sl"]+=1; monthly_stats[month_key]["sl"]+=1

    total = tp+sl
    wr = (tp/total*100) if total>0 else 0
    top = max(best.items(), key=lambda x:x[1]["tp"], default=("N/A",{}))
    stars = "⭐"*min(int(wr/20),5)

    # Top 3 meilleurs mois
    top_months = sorted(monthly_stats.items(),
        key=lambda x: x[1]["tp"]/(x[1]["tp"]+x[1]["sl"]+0.001), reverse=True)[:3]
    months_text = "\n".join([
        f"  🥇 {m[0]} — {m[1]['tp']}TP/{m[1]['sl']}SL"
        for m in top_months
    ])

    msg = (
        f"🏆 *BILAN ANNUEL — {today.year}*\n"
        f"{'═'*26}\n"
        f"✅ Signaux TP :    *{tp}*\n"
        f"❌ Signaux SL :    *{sl}*\n"
        f"🏹 TP niveaux touchés : *{total_tps_hit}*\n"
        f"📈 Total signaux : *{total}*\n"
        f"🎯 Winrate annuel : *{wr:.0f}%* {stars}\n"
        f"{'─'*26}\n"
        f"🏅 Meilleure paire : *{top[0]}*\n"
        f"📅 Meilleurs mois :\n{months_text}\n"
        f"{'─'*26}\n"
        f"{'🔥 ANNÉE EXCEPTIONNELLE !' if wr>=70 else '💪 Belle année !' if wr>=55 else '📚 Chaque année on s améliore !'}\n"
        f"{'═'*26}\n"
        f"_Merci pour votre fidélité toute l'année_ 🙏\n"
        f"_Rendez-vous l'année prochaine encore plus fort !_ 🚀"
    )
    telegram_send(msg)

def send_citation():     telegram_send(random.choice(CITATIONS))
def send_humour():       telegram_send(random.choice(HUMOUR))
def send_motivation():   telegram_send(random.choice(MOTIVATION))
def send_matin():        telegram_send(random.choice(MATIN))
def send_soir():         telegram_send(random.choice(SOIR))

def send_market_watch():
    signals = load(SIGNALS_FILE)
    actifs = [s for s in signals.values() if not s.get("closed")]
    n = len(actifs)
    session = get_session()

    if n == 0:
        msg = f"⏳ *Market Watch.* Pas de signal — la patience paie."
    else:
        lines = "\n".join([f"  → {s['symbol']} {s['direction']}" for s in actifs])
        msg = (
            f"📡 *MARKET WATCH*\n"
            f"{'─'*20}\n"
            f"{session}\n"
            f"🔎 {n} signal(s) actif(s) :\n{lines}\n"
            f"{'─'*20}\n"
            f"🕐 {datetime.now().strftime('%H:%M')} UTC"
        )
    telegram_send(msg)

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
    log.info("🚀 Sniper Bot V5 — SMC Edition — Démarrage...")

    schedule.every(1).hours.do(scan_markets)
    schedule.every(5).minutes.do(check_active_signals)
    schedule.every().day.at("21:00").do(daily_summary)
    schedule.every().monday.at("08:00").do(weekly_summary)
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

    # Bilan mensuel — 1er de chaque mois à 09h00
    if datetime.now().day == 1:
        schedule.every().day.at("09:00").do(monthly_summary)

    # Bilan annuel — 31 décembre à 20h00
    if datetime.now().month == 12 and datetime.now().day == 31:
        schedule.every().day.at("20:00").do(yearly_summary)

    scan_markets()

    log.info("✅ Sniper Bot V5 actif — SMC | Multi-TP | Réponse automatique")
    while True:
        schedule.run_pending()
        time.sleep(30)
