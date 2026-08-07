"""
Analyst Fish服务
提供一个可直接调用的市场分析人格 Agent
"""

import json
import re
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.analyst_fish')


DEFAULT_ANALYST_FISH_PERSONA: Dict[str, Any] = {
    "bio": "Software Engineer by day, Option Buyer by passion. Believes in the 'India Growth Story'. Every dip is a buying opportunity!",
    "persona": (
        "Rahul is a 28-year-old software developer based in Bengaluru. He grew up during the post-COVID bull run, "
        "meaning he has never experienced a prolonged, multi-year bear market. He trades actively using modern "
        "discount broker apps. Background: He allocates 40% of his monthly salary to aggressive SIPs in Small and "
        "Mid-cap mutual funds, but uses his bonus money to trade high-risk Nifty and BankNifty weekly options. "
        "Character Traits: He is an ESTP, action-oriented, risk-tolerant, and highly susceptible to FOMO. He is an "
        "optimist who gets easily excited by green market days and tends to panic-hold during red days, hoping for a "
        "quick V-shaped recovery. Behavioral Logic: Rahul gets most of his financial news from finfluencers on "
        "YouTube and Twitter rather than primary macro documents. His trading style is momentum and sentiment-driven. "
        "If he sees consecutive green candles or a breakout on a chart, he buys heavily. Stance & Views: He is a "
        "permabull. He strongly believes India is decoupled from the world and that domestic retail power will absorb "
        "foreign selling. Personal Memory: Rahul is sitting on a heavy loss in his IT sector portfolio due to poor "
        "earnings, but refuses to sell. In the face of a potential RBI rate hike, his immediate reaction is to wait "
        "for the market to drop and then buy call options at the bottom, anticipating a short-covering rally."
    ),
    "age": 28,
    "gender": "male",
    "mbti": "ESTP",
    "country": "India",
    "profession": "Retail F&O Trader / Software Engineer",
    "interested_topics": [
        "BankNifty Weekly Options",
        "Small and Mid-cap Breakouts",
        "Discount Broking Apps",
        "Technical Chart Patterns",
        "FinTwit Sentiments"
    ]
}


class AnalystFishAgent:
    """基于交易人格的轻量分析 Agent"""

    agent_name = "analyst_fish"

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def get_default_persona(self) -> Dict[str, Any]:
        """返回默认人设副本，避免被调用方原地修改"""
        return deepcopy(DEFAULT_ANALYST_FISH_PERSONA)

    def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        market_context: Optional[Any] = None,
        persona: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        与 analyst_fish 对话

        Args:
            message: 用户输入
            chat_history: 历史对话
            market_context: 额外市场上下文，可为字符串或JSON对象
            persona: 可选的人设覆盖字段
        """
        persona_payload = self._merge_persona(persona)
        messages = self._build_messages(
            message=message,
            chat_history=chat_history or [],
            market_context=market_context,
            persona=persona_payload
        )

        logger.info("analyst_fish 开始生成回复")
        response_mode = "llm"
        try:
            reply = self.llm_client.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
        except Exception as e:
            logger.warning(f"analyst_fish LLM调用失败，回退到规则模式: {e}")
            reply = self._generate_fallback_reply(
                message=message,
                market_context=market_context,
                persona=persona_payload
            )
            response_mode = "fallback"

        return {
            "agent_name": self.agent_name,
            "reply": reply,
            "persona": persona_payload,
            "response_mode": response_mode,
            "generated_at": datetime.now().isoformat()
        }

    def _merge_persona(self, persona: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        merged = self.get_default_persona()
        if not persona:
            return merged

        for key, value in persona.items():
            if value is None:
                continue
            merged[key] = value
        return merged

    def _build_messages(
        self,
        message: str,
        chat_history: List[Dict[str, str]],
        market_context: Optional[Any],
        persona: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(persona, market_context)
            }
        ]

        for item in chat_history:
            role = item.get("role", "").strip()
            content = item.get("content", "").strip()
            if role in {"system", "user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})
        return messages

    def _build_system_prompt(self, persona: Dict[str, Any], market_context: Optional[Any]) -> str:
        context_text = self._format_market_context(market_context)
        interested_topics = ", ".join(persona.get("interested_topics") or [])

        return (
            f"You are {self.agent_name}, a realistic market participant in the MiroFish world.\n"
            "Stay in character at all times.\n"
            "Do not present yourself as an AI assistant.\n"
            "Answer in a direct, conversational style consistent with the persona below.\n"
            "When the user asks for a market view, focus on sentiment, momentum, retail psychology, chart-led thinking, "
            "and practical trade reactions. Avoid generic disclaimers unless the user explicitly asks for risk advice.\n"
            "If information is missing, make the character's assumptions explicit instead of pretending certainty.\n\n"
            "Persona Profile:\n"
            f"- Bio: {persona.get('bio', '')}\n"
            f"- Detailed Persona: {persona.get('persona', '')}\n"
            f"- Age: {persona.get('age', '')}\n"
            f"- Gender: {persona.get('gender', '')}\n"
            f"- MBTI: {persona.get('mbti', '')}\n"
            f"- Country: {persona.get('country', '')}\n"
            f"- Profession: {persona.get('profession', '')}\n"
            f"- Interested Topics: {interested_topics}\n\n"
            "Behavioral Requirements:\n"
            "- Sound like a real Indian retail trader with conviction and momentum bias.\n"
            "- Lean bullish by default, especially on dips and breakout setups.\n"
            "- Reference practical market behavior, trader positioning, and sentiment shifts.\n"
            "- Keep replies useful for simulation and roleplay, not academic.\n"
            "- If asked to step out of character and analyze the persona, you may do so explicitly.\n\n"
            f"Market Context:\n{context_text}"
        )

    def _format_market_context(self, market_context: Optional[Any]) -> str:
        if market_context is None:
            return "No additional market context provided."

        if isinstance(market_context, str):
            stripped = market_context.strip()
            return stripped or "No additional market context provided."

        try:
            return json.dumps(market_context, ensure_ascii=False, indent=2)
        except TypeError:
            return str(market_context)

    def _generate_fallback_reply(
        self,
        message: str,
        market_context: Optional[Any],
        persona: Dict[str, Any]
    ) -> str:
        """在外部 LLM 不可用时，生成可用的角色化回复。"""
        lower = message.lower()
        context_text = self._format_market_context(market_context).lower()
        combined = f"{lower}\n{context_text}"

        sentiment = self._infer_sentiment(combined)
        trigger = self._infer_trigger(combined)
        action = self._infer_action_plan(sentiment, trigger)
        risk = self._infer_risk_note(sentiment, trigger)

        intro = (
            f"As {persona.get('profession', 'a retail trader')} from {persona.get('country', 'India')}, "
            "my first read is pure positioning and sentiment."
        )

        return (
            f"{intro}\n\n"
            f"My read: {sentiment}\n"
            f"Trigger I am focusing on: {trigger}\n"
            f"What I would do: {action}\n"
            f"What can go wrong: {risk}\n\n"
            "This is a fallback offline response because the configured LLM provider is unavailable, "
            "but the analyst_fish workflow is still functioning."
        )

    def _infer_sentiment(self, text: str) -> str:
        bearish_terms = [
            "down", "drop", "fall", "red", "selloff", "hike", "bearish",
            "panic", "crash", "dump", "weak", "breakdown", "volatility"
        ]
        bullish_terms = [
            "up", "green", "breakout", "rally", "recovery", "bounce",
            "support", "bullish", "strength", "squeeze"
        ]

        bearish_score = sum(1 for term in bearish_terms if term in text)
        bullish_score = sum(1 for term in bullish_terms if term in text)

        if bearish_score > bullish_score:
            return (
                "Short-term sentiment is shaken, but this is exactly the kind of fast fear move a momentum-heavy "
                "dip buyer tries to fade if the market stabilizes."
            )
        if bullish_score > bearish_score:
            return (
                "Sentiment is still constructive. The setup sounds like traders are leaning toward continuation "
                "and breakout participation."
            )
        return (
            "Sentiment looks mixed. I would treat this as a positioning-driven tape where retail conviction can flip quickly."
        )

    def _infer_trigger(self, text: str) -> str:
        trigger_map = [
            ("rbi", "RBI policy shock and how quickly traders reprice rate-sensitive sectors"),
            ("hike", "hawkish macro surprise and whether the first flush exhausts itself"),
            ("banknifty", "bank-heavy leadership, option premium expansion, and intraday reversals"),
            ("nifty", "index-level breadth, dip buying behavior, and whether support holds"),
            ("it", "earnings damage versus hope for a relief bounce"),
            ("breakout", "whether the breakout has real follow-through or is just FOMO chasing"),
            ("support", "if support attracts aggressive dip buyers quickly enough"),
        ]

        for keyword, description in trigger_map:
            if keyword in text:
                return description

        return "price reaction, retail psychology, and whether the first move gets absorbed or rejected"

    def _infer_action_plan(self, sentiment: str, trigger: str) -> str:
        if "shaken" in sentiment:
            return (
                "I would not blindly catch the first candle. I would wait for the panic leg to slow, then look for "
                "a reclaim or strong reversal before leaning into calls. If no rebound shows up, I stay light."
            )
        if "constructive" in sentiment:
            return (
                "I would stay with momentum, but only if the move keeps holding above breakout zones. If price keeps "
                "accepting higher levels, I would look for continuation instead of overthinking macro."
            )
        return (
            "I would trade smaller and react to confirmation. In a mixed tape, chasing is expensive, so I would wait "
            "for either a clean breakout or a flush-then-reclaim setup."
        )

    def _infer_risk_note(self, sentiment: str, trigger: str) -> str:
        if "hawkish" in trigger or "policy" in trigger:
            return (
                "The biggest risk is assuming a V-shaped recovery too early while policy repricing is still in progress."
            )
        if "breakout" in trigger:
            return "The biggest risk is buying a fake breakout after social sentiment gets overheated."
        if "support" in trigger:
            return "The biggest risk is support failing after multiple retests and trapping dip buyers."
        return "The biggest risk is confusing short-covering noise with a durable directional move."
