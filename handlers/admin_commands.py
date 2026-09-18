"""管理员命令处理器"""
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command

logger = logging.getLogger(__name__)


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /addbalance 命令 - 管理员增加积分"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    if not context.args or len(context.args) < 2:
        await message.reply_text(
            "使用方法: /addbalance <用户ID> <积分数量>\n\n示例: /addbalance 123456789 10"
        )
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if not db.user_exists(target_user_id):
            await message.reply_text("用户不存在。")
            return

        if db.add_balance(target_user_id, amount):
            user = db.get_user(target_user_id)
            await message.reply_text(
                f"✅ 成功为用户 {target_user_id} 增加 {amount} 积分。\n"
                f"当前积分：{user['balance']}"
            )
        else:
            await message.reply_text("操作失败，请稍后重试。")
    except ValueError:
        await message.reply_text("参数格式错误，请输入有效的数字。")


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /block 命令 - 管理员拉黑用户"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    if not context.args:
        await message.reply_text(
            "使用方法: /block <用户ID>\n\n示例: /block 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await message.reply_text("用户不存在。")
            return

        if db.block_user(target_user_id):
            await message.reply_text(f"✅ 已拉黑用户 {target_user_id}。")
        else:
            await message.reply_text("操作失败，请稍后重试。")
    except ValueError:
        await message.reply_text("参数格式错误，请输入有效的用户ID。")


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /white 命令 - 管理员取消拉黑"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    if not context.args:
        await message.reply_text(
            "使用方法: /white <用户ID>\n\n示例: /white 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await message.reply_text("用户不存在。")
            return

        if db.unblock_user(target_user_id):
            await message.reply_text(f"✅ 已将用户 {target_user_id} 移出黑名单。")
        else:
            await message.reply_text("操作失败，请稍后重试。")
    except ValueError:
        await message.reply_text("参数格式错误，请输入有效的用户ID。")


async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /blacklist 命令 - 查看黑名单"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    blacklist = db.get_blacklist()

    if not blacklist:
        await message.reply_text("黑名单为空。")
        return

    msg = "📋 黑名单列表：\n\n"
    for user in blacklist:
        msg += f"用户ID: {user['user_id']}\n"
        msg += f"用户名: @{user['username']}\n"
        msg += f"姓名: {user['full_name']}\n"
        msg += "---\n"

    await message.reply_text(msg)


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /genkey 命令 - 管理员生成卡密"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    if not context.args or len(context.args) < 2:
        await message.reply_text(
            "使用方法: /genkey <卡密> <积分> [使用次数] [过期天数]\n\n"
            "示例:\n"
            "/genkey wandouyu 20 - 生成20积分的卡密（单次使用，永不过期）\n"
            "/genkey vip100 50 10 - 生成50积分的卡密（可使用10次，永不过期）\n"
            "/genkey temp 30 1 7 - 生成30积分的卡密（单次使用，7天后过期）"
        )
        return

    try:
        key_code = context.args[0].strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 else None

        if balance <= 0:
            await message.reply_text("积分数量必须大于0。")
            return

        if max_uses <= 0:
            await message.reply_text("使用次数必须大于0。")
            return

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ 卡密生成成功！\n\n"
                f"卡密：{key_code}\n"
                f"积分：{balance}\n"
                f"使用次数：{max_uses}次\n"
            )
            if expire_days:
                msg += f"有效期：{expire_days}天\n"
            else:
                msg += "有效期：永久\n"
            msg += f"\n用户使用方法: /use {key_code}"
            await message.reply_text(msg)
        else:
            await message.reply_text("卡密已存在或生成失败，请更换卡密名称。")
    except ValueError:
        await message.reply_text("参数格式错误，请输入有效的数字。")


async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /listkeys 命令 - 管理员查看卡密列表"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    keys = db.get_all_card_keys()

    if not keys:
        await message.reply_text("暂无卡密。")
        return

    msg = "📋 卡密列表：\n\n"
    for key in keys[:20]:  # 只显示前20个
        msg += f"卡密：{key['key_code']}\n"
        msg += f"积分：{key['balance']}\n"
        msg += f"使用次数：{key['current_uses']}/{key['max_uses']}\n"

        if key["expire_at"]:
            expire_time = datetime.fromisoformat(key["expire_at"])
            if datetime.now() > expire_time:
                msg += "状态：已过期\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"状态：有效（剩余{days_left}天）\n"
        else:
            msg += "状态：永久有效\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n（仅显示前20个，共{len(keys)}个）"

    await message.reply_text(msg)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /broadcast 命令 - 管理员群发通知"""
    if await reject_group_command(update):
        return

    message = update.effective_message
    if not message:
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await message.reply_text("您没有权限使用此命令。")
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or ""

    if not text:
        await message.reply_text("使用方法: /broadcast <文本>，或回复一条消息后发送 /broadcast")
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = await message.reply_text(f"📢 开始广播，共 {len(user_ids)} 个用户...")

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
            await asyncio.sleep(0.05)  # 适当限速避免触发限制
        except Exception as e:
            logger.warning("广播到 %s 失败: %s", uid, e)
            failed += 1

    await status_msg.edit_text(f"✅ 广播完成！\n成功：{success}\n失败：{failed}")
