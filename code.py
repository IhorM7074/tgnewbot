
import requests
import logging
import numpy as np
import talib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Словари с текстами на разных языках ---
TEXTS = {
    'ru': {
        'start_message': "📊 Выберите действие или введите тикер или запрос (например: BTC, 12 SUI USDT):",
        'help_message_header': "💡 **Как использовать бота:**\n\n",
        'help_message_calculation_header': "**Для расчета стоимости:**\n",
        'help_message_calculation_text': "Введите количество и пару монет, например: `12 SUI USDT` или `0.5 ETH BTC`.\n"
                                        "- Бот вернет стоимость указанного количества первой монеты во второй валюте.\n"
                                        "- Для USDT пар, цена будет показана в долларах ($).\n"
                                        "- Для крипто-крипто пар (например, ETH BTC), цена будет показана во второй криптовалюте.\n\n",
        'help_message_calculation_examples_header': "**Примеры запросов для расчета:**\n",
        'help_message_calculation_examples_text': "- `12 SUI USDT` -  узнать стоимость 12 SUI в долларах США.\n"
                                                 "- `0.5 ETH BTC` - узнать стоимость 0.5 ETH в BTC.\n\n",
        'help_message_technical_analysis_header': "**Для получения технического анализа (калькулятор) с разными таймфреймами:**\n",
        'help_message_technical_analysis_text': "Просто введите тикер монеты (например, `BTC`, `ETH`, `SUI`). Бот покажет:\n"
                                                  "- Текущую цену (всегда)\n"
                                                  "- Изменение цены за выбранный таймфрейм в процентах\n"
                                                  "- Торговый сигнал и тренд для выбранного таймфрейма\n"
                                                  "- Кнопки для переключения на технический анализ для таймфреймов: 1ч, 4ч, 12ч, Назад\n"
                                                  "**Вы можете переключить язык бота на английский или русский, нажав соответствующие кнопки ниже.**\n\n", # Обновлено упоминание кнопок языков
        'help_message_technical_analysis_features_header': "**Поддерживаемые функции технического анализа:**\n",
        'help_message_technical_analysis_features_text': "- RSI (Индекс относительной силы)\n"
                                                          "- MACD (Схождение/расхождение скользящих средних)\n"
                                                          "- EMA (Экспоненциальная скользящая средняя) - 50 и 200 периодов\n"
                                                          "- Bollinger Bands (Полосы Боллинджера)\n"
                                                          "- Stochastic Oscillator (Стохастический осциллятор)\n"
                                                          "- SMA (Простая скользящая средняя) - 20 и 50 периодов\n"
                                                          "- Parabolic SAR (Параболическая система SAR)\n"
                                                          "- ADX (Индекс направленного движения)\n"
                                                          "- Ichimoku Cloud (Облако Ишимоку)\n"
                                                          "- Уровни поддержки и сопротивления\n\n",
        'help_message_other_functions_header': "**Другие функции:**\n",
        'help_message_other_functions_text': "- Раздел 'Топ 10 рост 🚀' и 'Топ 10 падения 📉' показывает лидеров роста и падения на Binance.\n"
                                               "- Раздел 'Помощь' - текущая справка.\n"
                                               "- Раздел 'Donat' - для поддержки разработчика.\n",
        'help_message_close_button': "Закрыть",
        'top10_rise_button': "Топ 10 рост 🚀",
        'top10_fall_button': "Топ 10 падения 📉",
        'help_button': "❓ Помощь",
        'donat_button': "💰 Donat",
        'back_button': "Назад",
        'english_button': "English",
        'russian_button': "Русский", # Добавлена кнопка "Русский"
        'top10_rise_header': "🚀 **Топ 10 монет рост (Binance):**\n\n",
        'top10_fall_header': "📉 **Топ 10 монет падения (Binance):**\n\n",
        'binance_data_unavailable_fallback_rise': "⚠️ Binance data unavailable, using CoinGecko trending as fallback for top 10 rising coins:\n\n",
        'binance_data_unavailable_fallback_fall': "⚠️ Binance data unavailable, using CoinGecko trending as fallback for top 10 falling coins:\n\n",
        'error_fetching_top10_rise': "⚠️ Error fetching top 10 rising coins.",
        'error_fetching_top10_fall': "⚠️ Error fetching top 10 falling coins.",
        'price_in_usdt': "{:.2f} $",
        'price_in_crypto': "{:.6f} {}",
        'error_fetching_price_usdt': "⚠️ Error fetching price for {} in USDT",
        'error_fetching_price_crypto': "⚠️ Error fetching price for {} in {}",
        'invalid_input_amount_coin_coin': "⚠️ Invalid input. Please use format: amount COIN1 COIN2 (e.g., 12 SUI USDT)",
        'invalid_input_amount_coin_coin_index_error': "⚠️ Invalid input. Please use format: amount COIN1 COIN2 (e.g., 12 SUI USDT)",
        'error_fetching_data': "⚠️ Error fetching data",
        'price_coin': "💰 **{} Price:** ${:.2f}\n",
        'change_24h': "📈 24h Change: {:.2f}%\n",
        'signal_24h': "🔔 **Signal (24h):** {}\n",
        'trend_24h': "📊 **Trend (24h):** {}",
        'button_1h': "1h",
        'button_4h': "4h",
        'button_12h': "12h",
        'not_enough_historical_data': "⚠️ Not enough historical data for this timeframe.",
        'timeframe_change': "📈 {} Change: {:.2f}%\n",
        'signal_timeframe': "🔔 **Signal ({}):** {}\n",
        'trend_timeframe': "📊 **Trend ({}):** {}",
        'error_fetching_timeframe_data': "⚠️ Error fetching data for timeframe.",
        'donat_message': "🙏 Поддержите разработчика, чтобы бот продолжал радовать вас новыми функциями и улучшениями!\n\n"
        
                         " **USDT (TRC20):** `TYndQoBjYDMn2r4GZ5JqYyS5oJvJ1tYLi7`\n\n" # Замените на свой USDT TRC20 адрес
                         
                          " **BTC:** `bc1qcategq6gf69ytjz9a8ldavy2yjuc6f67zexsns`\n" # 
                         
                          "Спасибо за вашу поддержку!",
        'language_switch_developing': "Функция переключения на английский в разработке!", # Временное сообщение
        'trend_ascending': "🟢 Восходящий",
        'trend_descending': "🔴 Нисходящий",
        'trend_sideways': "➖ Боковой",
        'trend_strength_strong': " (Сильный)",
        'trend_strength_weak': " (Слабый)",
        'signal_buy': "BUY 📈",
        'signal_sell': "SELL 📉",
        'signal_hold': "HOLD ⚖",
        'interval_1h': '1h',
        'interval_4h': '4h',
        'interval_8h': '8h', # Добавлено для 8h, хотя сейчас кнопка 4h
        'interval_12h': '12h',
        'interval_24h': '24h',
        'interval_1d': '24h', # или '1d', если хотите "1 day"
        'interval_change': 'Change',

    },
    'en': {
        'start_message': "📊 Choose an action or enter a ticker or request (e.g., BTC, 12 SUI USDT):",
        'help_message_header': "💡 **How to use the bot:**\n\n",
        'help_message_calculation_header': "**For price calculation:**\n",
        'help_message_calculation_text': "Enter the amount and coin pair, for example: `12 SUI USDT` or `0.5 ETH BTC`.\n"
                                        "- The bot will return the value of the specified amount of the first coin in the second currency.\n"
                                        "- For USDT pairs, the price will be shown in dollars ($).\n"
                                        "- For crypto-crypto pairs (e.g., ETH BTC), the price will be shown in the second cryptocurrency.\n\n",
        'help_message_calculation_examples_header': "**Examples of calculation requests:**\n",
        'help_message_calculation_examples_text': "- `12 SUI USDT` - find out the cost of 12 SUI in US dollars.\n"
                                                 "- `0.5 ETH BTC` - find out the cost of 0.5 ETH in BTC.\n\n",
        'help_message_technical_analysis_header': "**To get technical analysis (calculator) with different timeframes:**\n",
        'help_message_technical_analysis_text': "Just enter the coin ticker (e.g., `BTC`, `ETH`, `SUI`). The bot will show:\n"
                                                  "- Current price (always)\n"
                                                  "- Price change for the selected timeframe in percent\n"
                                                  "- Trading signal and trend for the selected timeframe\n"
                                                  "- Buttons to switch to technical analysis for timeframes: 1h, 4h, 12h, Back\n"
                                                  "**You can switch the bot language to English or Russian by pressing the corresponding buttons below.**\n\n", # Обновлено упоминание кнопок языков
        'help_message_technical_analysis_features_header': "**Supported technical analysis functions:**\n",
        'help_message_technical_analysis_features_text': "- RSI (Relative Strength Index)\n"
                                                          "- MACD (Moving Average Convergence/Divergence)\n"
                                                          "- EMA (Exponential Moving Average) - 50 and 200 periods\n"
                                                          "- Bollinger Bands\n"
                                                          "- Stochastic Oscillator\n"
                                                          "- SMA (Simple Moving Average) - 20 and 50 periods\n"
                                                          "- Parabolic SAR (Parabolic SAR system)\n"
                                                          "- ADX (Average Directional Index)\n"
                                                          "- Ichimoku Cloud\n"
                                                          "- Support and resistance levels\n\n",
        'help_message_other_functions_header': "**Other functions:**\n",
        'help_message_other_functions_text': "- The 'Top 10 Rise 🚀' and 'Top 10 Fall 📉' sections show the top gainers and losers on Binance.\n"
                                               "- The 'Help' section - current help.\n"
                                               "- The 'Donat' section - to support the developer.\n",
        'help_message_close_button': "Close",
        'top10_rise_button': "Top 10 Rise 🚀",
        'top10_fall_button': "Top 10 Fall 📉",
        'help_button': "❓ Help",
        'donat_button': "💰 Donate",
        'back_button': "Back",
        'english_button': "English",
        'russian_button': "Russian", # Добавлена кнопка "Русский"
        'top10_rise_header': "🚀 **Top 10 Rising Coins (Binance):**\n\n",
        'top10_fall_header': "📉 **Top 10 Falling Coins (Binance):**\n\n",
        'binance_data_unavailable_fallback_rise': "⚠️ Binance data unavailable, using CoinGecko trending as fallback for top 10 rising coins:\n\n",
        'binance_data_unavailable_fallback_fall': "⚠️ Binance data unavailable, using CoinGecko trending as fallback for top 10 falling coins:\n\n",
        'error_fetching_top10_rise': "⚠️ Error fetching top 10 rising coins.",
        'error_fetching_top10_fall': "⚠️ Error fetching top 10 falling coins.",
        'price_in_usdt': "{:.2f} $",
        'price_in_crypto': "{:.6f} {}",
        'error_fetching_price_usdt': "⚠️ Error fetching price for {} in USDT",
        'error_fetching_price_crypto': "⚠️ Error fetching price for {} in {}",
        'invalid_input_amount_coin_coin': "⚠️ Invalid input. Please use format: amount COIN1 COIN2 (e.g., 12 SUI USDT)",
        'invalid_input_amount_coin_coin_index_error': "⚠️ Invalid input. Please use format: amount COIN1 COIN2 (e.g., 12 SUI USDT)",
        'error_fetching_data': "⚠️ Error fetching data",
        'price_coin': "💰 **{} Price:** ${:.2f}\n",
        'change_24h': "📈 24h Change: {:.2f}%\n",
        'signal_24h': "🔔 **Signal (24h):** {}\n",
        'trend_24h': "📊 **Trend (24h):** {}",
        'button_1h': "1h",
        'button_4h': "4h",
        'button_12h': "12h",
        'not_enough_historical_data': "⚠️ Not enough historical data for this timeframe.",
        'timeframe_change': "📈 {} Change: {:.2f}%\n",
        'signal_timeframe': "🔔 **Signal ({}):** {}\n",
        'trend_timeframe': "📊 **Trend ({}):** {}",
        'error_fetching_timeframe_data': "⚠️ Error fetching data for timeframe.",
        'donat_message': "🙏 Support the developer so that the bot continues to delight you with new features and improvements!\n\n"
                         # Замените на свой QIWI номер
                         " **USDT (TRC20):** `TYndQoBjYDMn2r4GZ5JqYyS5oJvJ1tYLi7`\n\n"
                          " **BTC:** `bc1qcategq6gf69ytjz9a8ldavy2yjuc6f67zexsns`\n" 
                         "Thank you for your support!",
        'language_switch_developing': "Language switch to English is under development!", # Временное сообщение
        'trend_ascending': "🟢 Ascending",
        'trend_descending': "🔴 Descending",
        'trend_sideways': "➖ Sideways",
        'trend_strength_strong': " (Strong)",
        'trend_strength_weak': " (Weak)",
        'signal_buy': "BUY 📈",
        'signal_sell': "SELL 📉",
        'signal_hold': "HOLD ⚖",
        'interval_1h': '1h',
        'interval_4h': '4h',
        'interval_8h': '8h', # Добавлено для 8h, хотя сейчас кнопка 4h
        'interval_12h': '12h',
        'interval_24h': '24h',
        'interval_1d': '24h', # или '1d', если хотите "1 day"
        'interval_change': 'Change',
    },
}

# --- Глобальная переменная для языка ---
BOT_LANGUAGE = 'ru'  # По умолчанию русский язык


def get_binance_price(coin_id: str):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {'symbol': f"{coin_id.upper()}USDT"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        ticker = response.json()
        return ticker
    except Exception as e:
        logger.error(f"Binance error: {e}")
        return None

def get_binance_price_direct(coin1_id: str, coin2_id: str):
    try:
        symbol = f"{coin1_id.upper()}{coin2_id.upper()}"
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': symbol}
        response = requests.get(url, params=params)
        response.raise_for_status()
        price_data = response.json()
        return float(price_data['price'])
    except Exception as e:
        logger.error(f"Binance direct price error: {e}")
        return None


def get_trending_coins():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [
            (coin["item"]["symbol"].upper(),
             coin["item"]["name"],
             float(coin["item"]["data"]["price"].replace(',', '')),  # Convert to float and remove commas
             float(coin["item"]["data"]["price_change_percentage_24h"]["usd"]))
            for coin in data["coins"][:10]  # Get top 10 trending coins
        ]
    except Exception as e:
        logger.error(f"Coingecko error: {e}")
        return None


def get_binance_top_movers(limit=10, sort_by='priceChangePercent', ascending=False):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url)
        response.raise_for_status()
        tickers = response.json()

        # Filter USDT pairs and remove pairs without USDT
        usdt_tickers = [
            ticker for ticker in tickers if ticker['symbol'].endswith('USDT') and ticker['symbol'] != 'USDTUSDT'
        ]

        # Sort tickers
        sorted_tickers = sorted(
            usdt_tickers,
            key=lambda x: float(x[sort_by]),
            reverse=not ascending  # ascending=False for рост (по убыванию), ascending=True для падения (по возрастанию)
        )

        top_movers = []
        for ticker in sorted_tickers[:limit]:
            symbol = ticker['symbol'].replace('USDT', '')
            top_movers.append((
                symbol,
                symbol,  # Используем символ как имя для совместимости
                float(ticker['lastPrice']),
                float(ticker['priceChangePercent'])
            ))
        return top_movers

    except Exception as e:
        logger.error(f"Binance top movers error: {e}")
        return None


def get_coingecko_top_movers_fallback(limit=10, sort_by_index=3, ascending=False):
    trending_coins = get_trending_coins() # Используем трендовые монеты как fallback
    if trending_coins:
        sorted_coins = sorted(
            trending_coins,
            key=lambda x: x[sort_by_index],
            reverse=not ascending
        )
        return sorted_coins[:limit]
    return None


async def handle_top10_rise(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    top_risers = get_binance_top_movers(sort_by='priceChangePercent', ascending=False)

    if not top_risers:
        top_risers = get_coingecko_top_movers_fallback(sort_by_index=3, ascending=False)
        if not top_risers:
            await query.edit_message_text(TEXTS[BOT_LANGUAGE]['error_fetching_top10_rise'])
            return
        else:
            message = TEXTS[BOT_LANGUAGE]['binance_data_unavailable_fallback_rise']
    else:
        message = TEXTS[BOT_LANGUAGE]['top10_rise_header']

    for coin in top_risers:
        coin_id, coin_name, price, change_24h = coin
        message += (f"📈 **{coin_name} ({coin_id})**: ${price:.2f}\n"
                    f"📈 24h Change: {change_24h:+.2f}%\n\n")

    await query.edit_message_text(message, parse_mode="Markdown")


async def handle_top10_fall(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    top_fallers = get_binance_top_movers(sort_by='priceChangePercent', ascending=True)

    if not top_fallers:
        top_fallers = get_coingecko_top_movers_fallback(sort_by_index=3, ascending=True)
        if not top_fallers:
            await query.edit_message_text(TEXTS[BOT_LANGUAGE]['error_fetching_top10_fall'])
            return
        else:
            message = TEXTS[BOT_LANGUAGE]['binance_data_unavailable_fallback_fall']
    else:
        message = TEXTS[BOT_LANGUAGE]['top10_fall_header']

    for coin in top_fallers:
        coin_id, coin_name, price, change_24h = coin
        message += (f"📉 **{coin_name} ({coin_id})**: ${price:.2f}\n"
                    f"📉 24h Change: {change_24h:+.2f}%\n\n")

    await query.edit_message_text(message, parse_mode="Markdown")


def calculate_indicators(prices, high, low, close, volume):
    if len(prices) < 50:
        return None

    indicators = {
        'rsi': talib.RSI(np.array(prices), timeperiod=14)[-1],
        'macd': talib.MACD(np.array(prices))[0][-1],
        'signal': talib.MACD(np.array(prices))[1][-1],
        'ema_50': talib.EMA(np.array(prices), 50)[-1],
        'ema_200': talib.EMA(np.array(prices), 200)[-1],
        'upper_bb': talib.BBANDS(np.array(prices), timeperiod=20)[0][-1],
        'lower_bb': talib.BBANDS(np.array(prices), timeperiod=20)[2][-1],
        'stoch_k': talib.STOCH(np.array(high), np.array(low), np.array(close))[0][-1],
        'stoch_d': talib.STOCH(np.array(high), np.array(low), np.array(close))[1][-1],
        'sma_20': talib.SMA(np.array(prices), 20)[-1],
        'sma_50': talib.SMA(np.array(prices), 50)[-1],
        'sar': talib.SAR(np.array(high), np.array(low))[-1],
        'volume': volume[-1]
    }
    return indicators


def calculate_support_resistance(prices, period=14):
    if len(prices) < period:
        return None, None

    supports = []
    resistances = []

    for i in range(period, len(prices)):
        window = prices[i - period:i]
        support = np.min(window)
        resistance = np.max(window)
        supports.append(support)
        resistances.append(resistance)

    return supports[-1] if supports else None, resistances[-1] if resistances else None


def calculate_adx(high, low, close, period=14):
    if len(close) < period:
        return None
    adx = talib.ADX(np.array(high), np.array(low), np.array(close), timeperiod=period)[-1]
    return adx


def calculate_ichimoku(high, low, close):
    if len(close) < 52:  # Минимум для расчета Ichimoku
        return None, None, None
    conversion_line = talib.MAX(np.array(high), timeperiod=9) + talib.MIN(np.array(low), timeperiod=9) / 2
    base_line = talib.MAX(np.array(high), timeperiod=26) + talib.MIN(np.array(low), timeperiod=26) / 2
    leading_span_a = (conversion_line + base_line) / 2
    leading_span_b = talib.MAX(np.array(high), timeperiod=52) + talib.MIN(np.array(low), timeperiod=52) / 2
    return conversion_line[-1], base_line[-1], leading_span_b[-1]


def determine_trend(ema_50, ema_200, current_price, previous_price):
    trend_text = ""
    strength_text = ""

    if ema_50 and ema_200:
        if ema_50 > ema_200:
            trend_text += TEXTS[BOT_LANGUAGE]['trend_ascending']
        else:
            trend_text += TEXTS[BOT_LANGUAGE]['trend_descending']

    if current_price and previous_price:
        price_change = current_price - previous_price
        if abs(price_change) > 0.05 * current_price:
            strength_text = TEXTS[BOT_LANGUAGE]['trend_strength_strong']
        else:
            strength_text = TEXTS[BOT_LANGUAGE]['trend_strength_weak']
        if price_change > 0:
            trend_text += " 📈"
        else:
            trend_text += " 📉"

    return trend_text + strength_text if trend_text else TEXTS[BOT_LANGUAGE]['trend_sideways']


def get_trading_signal(coin_id: str, interval='1d'):
    hist_data = get_historical_data(coin_id, interval) # Pass interval to historical data function
    if not hist_data or len(hist_data) < 50:
        return TEXTS[BOT_LANGUAGE]['error_fetching_data'], ""

    high = [h for h, _, _, _ in hist_data]
    low = [l for _, l, _, _ in hist_data]
    close = [c for _, _, c, _ in hist_data]
    volume = [v for _, _, _, v in hist_data]
    prices = close

    indicators = calculate_indicators(prices, high, low, close, volume)
    support, resistance = calculate_support_resistance(prices)

    buy_signals = sell_signals = 0

    # Сигналы на основе индикаторов (уже в вашем коде)
    if close[-1] <= indicators['lower_bb']:
        buy_signals += 1
    elif close[-1] >= indicators['upper_bb']:
        sell_signals += 1

    if indicators['stoch_k'] < 20:
        buy_signals += 1
    elif indicators['stoch_k'] > 80:
        sell_signals += 1

    if indicators['sma_20'] > indicators['sma_50']:
        buy_signals += 1
    elif indicators['sma_20'] < indicators['sma_50']:
        sell_signals += 1

    if indicators['volume'] > np.mean(volume[-5:]) * 1.5:
        if close[-1] > close[-2]:
            buy_signals += 1
        else:
            sell_signals += 1

    if close[-1] > indicators['sar']:
        buy_signals += 1
    else:
        sell_signals += 1

    if support and resistance:
        if close[-1] <= support * 1.005:
            buy_signals += 1
        elif close[-1] >= resistance * 0.995:
            sell_signals += 1

    if indicators['rsi'] > 70:
        sell_signals += 1
    elif indicators['rsi'] < 30:
        buy_signals += 1

    if indicators['macd'] > indicators['signal']:
        buy_signals += 1
    elif indicators['macd'] < indicators['signal']:
        sell_signals += 1

    if indicators['ema_50'] > indicators['ema_200']:
        buy_signals += 1
    elif indicators['ema_50'] < indicators['ema_200']:
        sell_signals += 1

    # Новые сигналы:
    # ADX
    adx = calculate_adx(high, low, close)
    if adx and adx > 25:
        buy_signals += 1

    # Ichimoku
    conversion_line, base_line, leading_span_b = calculate_ichimoku(high, low, close)
    if conversion_line and base_line and leading_span_b:
        if close[-1] > conversion_line and close[-1] > base_line:
            buy_signals += 1
        elif close[-1] < conversion_line and close[-1] < base_line:
            sell_signals += 1

    signal_text = TEXTS[BOT_LANGUAGE]['signal_buy'] if buy_signals > sell_signals else TEXTS[BOT_LANGUAGE]['signal_sell'] if sell_signals > buy_signals else TEXTS[BOT_LANGUAGE]['signal_hold']

    trend = determine_trend(
        indicators['ema_50'],
        indicators['ema_200'],
        close[-1],
        close[-2] if len(close) > 1 else None
    )

    return signal_text, trend


def get_historical_data(coin_id: str, interval='1d'): # Added interval parameter
    try:
        if interval == '24h': # Исправление: использовать '1d' для 24h
            binance_interval = '1d'
        elif interval == '8h':
            binance_interval = '8h'
        elif interval == '4h': # Добавлено для 4h
            binance_interval = '4h'
        else:
            binance_interval = interval

        url = f"https://api.binance.com/api/v3/klines?symbol={coin_id}USDT&interval={binance_interval}&limit=200" # Use interval in API request
        print(f"URL для исторических данных: {url}") # Вывод URL для отладки
        response = requests.get(url)
        response.raise_for_status()
        hist_data_json = response.json()
        print(f"Получены исторические данные ({interval}): {hist_data_json[:5]}") # Вывод первых 5 элементов для отладки
        return [
            (float(c[2]),  # high
             float(c[3]),  # low
             float(c[4]),  # close
             float(c[5]))  # volume
            for c in hist_data_json
        ]
    except Exception as e:
        logger.error(f"Historical data error: {e}")
        return None


async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip().upper()
    parts = text.split()

    if len(parts) >= 3: # Check if it's a calculation request (amount COIN1 COIN2)
        try:
            amount = float(parts[0])
            coin1_id = parts[1]
            coin2_id = parts[2]

            if coin2_id.upper() == "USDT":
                price_data = get_binance_price(coin1_id)
                if price_data:
                    price_usdt = float(price_data['lastPrice'])
                    calculated_value = amount * price_usdt
                    message = TEXTS[BOT_LANGUAGE]['price_in_usdt'].format(calculated_value)
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text(TEXTS[BOT_LANGUAGE]['error_fetching_price_usdt'].format(coin1_id))

            else: # Calculate in terms of another crypto (not USDT)
                direct_price = get_binance_price_direct(coin1_id, coin2_id)
                if direct_price:
                    calculated_value = amount * direct_price
                    message = TEXTS[BOT_LANGUAGE]['price_in_crypto'].format(calculated_value, coin2_id.upper()) # More decimal places for crypto-crypto pairs
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text(TEXTS[BOT_LANGUAGE]['error_fetching_price_crypto'].format(coin1_id, coin2_id))


        except ValueError:
            await update.message.reply_text(TEXTS[BOT_LANGUAGE]['invalid_input_amount_coin_coin'])
        except IndexError:
            await update.message.reply_text(TEXTS[BOT_LANGUAGE]['invalid_input_amount_coin_coin_index_error'])


    else: # Обработка как одиночный тикер для калькулятора (технический анализ)
        coin_id = text
        price_data = get_binance_price(coin_id)

        if not price_data:
            await update.message.reply_text(TEXTS[BOT_LANGUAGE]['error_fetching_data'])
            return

        price = float(price_data['lastPrice'])
        change_24h = float(price_data['priceChangePercent'])
        high = float(price_data['highPrice'])
        low = float(price_data['lowPrice'])

        signal_text, trend_text = get_trading_signal(coin_id) # Default 1d interval

        message = (TEXTS[BOT_LANGUAGE]['price_coin'].format(coin_id, price) +
                   TEXTS[BOT_LANGUAGE]['change_24h'].format(change_24h) +
                   TEXTS[BOT_LANGUAGE]['signal_24h'].format(signal_text) +
                   TEXTS[BOT_LANGUAGE]['trend_24h'].format(trend_text))

        keyboard = [
            [
                InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_1h'], callback_data=f"{coin_id}_1h"), # Callback data: TICKER_INTERVAL
                InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_4h'], callback_data=f"{coin_id}_4h"), # Возвращена кнопка 4h
            ],
            [
                InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_12h'], callback_data=f"{coin_id}_12h"),
                InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['back_button'], callback_data=f"{coin_id}_back"), # Кнопка "Назад"
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_timeframe_data(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_") # Parse callback data: TICKER_INTERVAL
    coin_id = data[0]
    interval = data[1]

    if interval == 'back': # Обработка кнопки "Назад"
        await query.edit_message_reply_markup(reply_markup=None) # Удаление кнопок
        return


    print(f"Выбран таймфрейм: {interval}") # Вывод выбранного интервала для отладки

    hist_data = get_historical_data(coin_id, interval) # Get historical data for the selected interval
    if not hist_data or len(hist_data) < 2: # Need at least two points to calculate change
        await query.edit_message_text(TEXTS[BOT_LANGUAGE]['not_enough_historical_data'])
        return

    # Calculate percentage change for the selected interval
    if interval == '4h': # Изменен расчет для 4h интервала
        if len(hist_data) >= 2:
            first_price = hist_data[1][2] # Цена закрытия 4ч свечи *перед* последней
            last_price = hist_data[0][2]  # Цена закрытия *последней* 4ч свечи
            interval_change_percent = ((last_price - first_price) / first_price) * 100
        else:
            interval_change_percent = 0.0 # Или можно обработать как ошибку
    else: # Для остальных интервалов - старый расчет (изменение за весь период)
        first_price = hist_data[-1][2] # Самая старая цена закрытия
        last_price = hist_data[0][2]  # Самая новая цена закрытия
        interval_change_percent = ((last_price - first_price) / first_price) * 100


    print(f"Таймфрейм: {interval}, Первая цена: {first_price}, Последняя цена: {last_price}, Процент изменения: {interval_change_percent:.2f}%") #  <<<---  ДОБАВЛЕНА ОТЛАДКА


    signal_text, trend_text = get_trading_signal(coin_id, interval) # Get signal for specific interval
    price_data = get_binance_price(coin_id) # Get current price for header

    if not price_data: # Handle error if price data is not available
        await query.edit_message_text(TEXTS[BOT_LANGUAGE]['error_fetching_timeframe_data'])
        return

    price = float(price_data['lastPrice'])


    message = (TEXTS[BOT_LANGUAGE]['price_coin'].format(coin_id, price) +
               TEXTS[BOT_LANGUAGE]['timeframe_change'].format(get_interval_label(interval, BOT_LANGUAGE), interval_change_percent) +
               TEXTS[BOT_LANGUAGE]['signal_timeframe'].format(interval, signal_text) +
               TEXTS[BOT_LANGUAGE]['trend_timeframe'].format(interval, trend_text))

    keyboard = [ # Re-create keyboard with 4h and "Back"
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_1h'], callback_data=f"{coin_id}_1h"),
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_4h'], callback_data=f"{coin_id}_4h"), # Возвращена кнопка 4h
        ],
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['button_12h'], callback_data=f"{coin_id}_12h"),
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['back_button'], callback_data=f"{coin_id}_back"), # Кнопка "Назад"
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)


    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup) # Re-add reply_markup to edit_message_text

def get_interval_label(interval, lang='ru'): # Функция для получения лейбла интервала с учетом языка
    interval_labels = {
        'ru': {
            '1h': TEXTS['ru']['interval_1h'],
            '4h': TEXTS['ru']['interval_4h'],
            '8h': TEXTS['ru']['interval_8h'],
            '12h': TEXTS['ru']['interval_12h'],
            '24h': TEXTS['ru']['interval_24h'],
            '1d': TEXTS['ru']['interval_1d'],
            'Change': TEXTS['ru']['interval_change'],
        },
        'en': {
            '1h': TEXTS['en']['interval_1h'],
            '4h': TEXTS['en']['interval_4h'],
            '8h': TEXTS['en']['interval_8h'],
            '12h': TEXTS['en']['interval_12h'],
            '24h': TEXTS['en']['interval_24h'],
            '1d': TEXTS['en']['interval_1d'],
            'Change': TEXTS['en']['interval_change'],
        }
    }
    return interval_labels[lang].get(interval, TEXTS[lang]['interval_change'])


async def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['top10_rise_button'], callback_data="TOP10_RISE"),
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['top10_fall_button'], callback_data="TOP10_FALL"),
        ],
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['help_button'], callback_data="HELP"),
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['donat_button'], callback_data="DONAT"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        TEXTS[BOT_LANGUAGE]['start_message'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def help(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    message = (TEXTS[BOT_LANGUAGE]['help_message_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_calculation_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_calculation_text'] +
               TEXTS[BOT_LANGUAGE]['help_message_calculation_examples_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_calculation_examples_text'] +
               TEXTS[BOT_LANGUAGE]['help_message_technical_analysis_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_technical_analysis_text'] +
               TEXTS[BOT_LANGUAGE]['help_message_technical_analysis_features_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_technical_analysis_features_text'] +
               TEXTS[BOT_LANGUAGE]['help_message_other_functions_header'] +
               TEXTS[BOT_LANGUAGE]['help_message_other_functions_text'])

    keyboard = [ # Обновленная клавиатура "Помощи" с кнопками "English" и "Русский"
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['help_message_close_button'], callback_data="CLOSE_HELP"), # Пример кнопки "Закрыть" (опционально)
        ],
        [
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['english_button'], callback_data="HELP_EN"), # Кнопка "English"
            InlineKeyboardButton(TEXTS[BOT_LANGUAGE]['russian_button'], callback_data="HELP_RU") # Кнопка "Русский"
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_donat(update: Update, context: CallbackContext):
    message = TEXTS[BOT_LANGUAGE]['donat_message']
    await update.callback_query.message.reply_text(message, parse_mode="Markdown")


async def button(update: Update, context: CallbackContext):
    global BOT_LANGUAGE  # <----  Перенесено объявление global в начало функции
    query = update.callback_query
    if query.data == "TOP10_RISE":
        await handle_top10_rise(update, context)
    elif query.data == "TOP10_FALL":
        await handle_top10_fall(update, context)
    elif query.data == "HELP":
        await help(update, context)
    elif query.data == "DONAT":
        await handle_donat(update, context)
    elif query.data == "HELP_EN":  # Обработка кнопки "English"
        BOT_LANGUAGE = 'en'
        await help(update, context)
        await query.answer(text="Bot language switched to English!")
    elif query.data == "HELP_RU":  # Обработка кнопки "Русский"
        BOT_LANGUAGE = 'ru'
        await help(update, context)
        await query.answer(text="Язык бота переключен на русский!")
    elif "_" in query.data:  # Handle timeframe button presses
        await handle_timeframe_data(update, context)
    elif query.data == "CLOSE_HELP":  # Обработка кнопки "Закрыть"
        await close_help(update, context)


async def close_help(update: Update, context: CallbackContext): # Пример обработчика для кнопки "Закрыть" (опционально)
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None) # Удаление кнопок


def main():
    application = Application.builder().token("7418232840:AAEhnpL7h-ZZpsYfJkgeeQVChojTc0gY8pw").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == "__main__":
    main()

