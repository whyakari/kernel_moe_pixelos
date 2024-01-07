import subprocess
import time
import glob
import os
import sys
import argparse
from pyrogram import filters
from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

load_dotenv()

elapsed_minutes = 0
elapsed_seconds = 0
elapsed_minutes_formatted = ""

chat_id = int(os.getenv('CHAT_ID', 0))
api_id = int(os.getenv('API_ID', 0))
api_hash = os.getenv('API_HASH', '')
bot_token = os.getenv('BOT_TOKEN', '')

app = Client(
    name="cache",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)

commit_head = subprocess.check_output(
    "git log --oneline -1 --pretty=format:'%h - %an'", 
    shell=True).decode().strip()
commit_id = subprocess.check_output(
    "git log --oneline -1 --pretty=format:'%h'", 
    shell=True).decode().strip()

author_name = commit_head.split(" - ")[1]
commit_hash = commit_head.split(" - ")[0]

kernel_version = subprocess.check_output(
    "make kernelversion 2>/dev/null", 
    shell=True).decode().strip()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-t", "--build-type",
    choices=["dev", "release"],
    default="release",
    help="Specify the build type (dev or release)"
)

args = parser.parse_args()
build_type = args.build_type

tag = f"ginkgo_{commit_hash[:7]}_{time.strftime('%Y%m%d')}"

@app.on_message(filters.command("compile") & filters.user(chat_id))
async def send_message_compiled(bot: Client, msg: Message):
    global elapsed_minutes, elapsed_seconds, elapsed_minutes_formatted
 
    start_time = time.perf_counter()
    start_message = await bot.send_message(
        chat_id, 
        "Compilation started, please wait."
    )

    return_code = subprocess.call(
        "./ksu_update.sh -t stable -k y", 
        shell=True
    )
    return_code = subprocess.call(
        "./build.sh", 
        shell=True
    )

    if return_code == 0:
        commit_head = subprocess.check_output("git log --oneline -1 --pretty=format:'%h - %an'", shell=True).decode().strip()
        commit_id = subprocess.check_output("git log --oneline -1 --pretty=format:'%h'", shell=True).decode().strip()

        author_name = commit_head.split(" - ")[1]
        commit_hash = commit_head.split(" - ")[0]
        
        message_commit = subprocess.check_output("git log --oneline -1", shell=True).decode().strip().split(" ")[1:]
        commit_text = " ".join(message_commit)
        commit_link = f'<a href="https://github.com/whyakari/kernel_moe_pixelos/commit/{commit_hash}">{commit_head}</a>'

        elapsed_time = int(time.perf_counter() - start_time)
        elapsed_minutes = elapsed_time // 60
        elapsed_seconds = elapsed_time % 60
 
        elapsed_minutes_formatted = "{:.2f}".format(
            elapsed_minutes + elapsed_seconds / 60
        )

        completion_message = f"\nCompleted in {elapsed_minutes_formatted} minute(s) and {elapsed_seconds} second(s) !"

        completed_compile_text = f"**Compilation completed!**\n\nCommit: {commit_link}\n{completion_message}"

        await start_message.edit_text(text=completed_compile_text)

        zip_files = glob.glob("*.zip")
        if zip_files:
            zip_file = zip_files[0]

            caption = f"""**Build Information**
 • **Commit**: `{commit_id}`
 • **Message**: `{commit_text}`
 • **Author**: `{author_name}`"""

            await bot.send_document(
                chat_id,
                zip_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
        sys.exit(0)

    else:
        await bot.send_message(
            chat_id, 
            "No zip files found in the current directory."
        )
        sys.exit(0)

print("bot is runnig...")        
app.run()
