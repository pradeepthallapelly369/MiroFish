"""
Analyst Agent API路由
提供 analyst_fish 的对话与默认人设接口
"""

import traceback
from flask import request, jsonify

from . import analyst_bp
from ..services.analyst_fish_agent import AnalystFishAgent
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.analyst')


@analyst_bp.route('/persona', methods=['GET'])
def get_default_persona():
    """获取 analyst_fish 默认人设"""
    try:
        agent = AnalystFishAgent()
        return jsonify({
            "success": True,
            "data": {
                "agent_name": agent.agent_name,
                "persona": agent.get_default_persona()
            }
        })
    except Exception as e:
        logger.error(f"获取 analyst_fish 默认人设失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@analyst_bp.route('/chat', methods=['POST'])
def chat_with_analyst():
    """与 analyst_fish 对话"""
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "success": False,
                "error": "Please provide a message"
            }), 400

        agent = AnalystFishAgent()
        result = agent.chat(
            message=message,
            chat_history=data.get("chat_history"),
            market_context=data.get("market_context"),
            persona=data.get("persona")
        )

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"analyst_fish 对话失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
