from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import Update
import os
from PIL import Image
from rembg import remove

TOKEN = "" #add the token here

#change the paths
ORG_PATH = ".\orgin"
EDIT_PATH = ".\edit"


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    message = "Hi there! I'm a background removal bot. To get started, please use the /start command.\nTo remove the background from an image, simply send the image to me."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a start message."""
    message = "To remove the background from an image, please send it to get started."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def process_image(photo_name: str) -> str:
    """Process the image and remove the background."""
    name, _ = os.path.splitext(photo_name)
    output_photo_path = os.path.join(EDIT_PATH, f"edit{name}.png")
    input_path = os.path.join(ORG_PATH, photo_name)

    with Image.open(input_path) as img:
        output = remove(img)
        output.save(output_photo_path)

    os.remove(input_path)
    return output_photo_path


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    if filters.PHOTO.check_update(update):
        file_id = update.message.photo[-1].file_id
        unique_file_id = update.message.photo[-1].file_unique_id
        photo_name = f"{unique_file_id}.jpg"
    elif filters.Document.IMAGE.check_update(update):
        file_id = update.message.document.file_id
        unique_file_id = update.message.document.file_unique_id
        _, f_ext = os.path.splitext(update.message.document.file_name)
        photo_name = f"{unique_file_id}{f_ext}"

    photo_file = await context.bot.get_file(file_id)
    await photo_file.download_to_drive(custom_path=os.path.join(ORG_PATH, photo_name))

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Your image is currently being processed. Please wait a moment.",
    )

    processed_image = await process_image(photo_name)
    await context.bot.send_document(
        chat_id=update.effective_chat.id, document=processed_image
    )

    sticker_image = Image.open(processed_image)
    name2, _ = os.path.splitext(processed_image)
    sticker_path = f"{name2}.webp"
    sticker_image.save(sticker_path)
    with open(sticker_path, "rb") as sticker_file:
        await context.bot.send_sticker(
            chat_id=update.effective_chat.id, sticker=sticker_file
        )
    os.remove(sticker_path)
    os.remove(processed_image)


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    help_handler = CommandHandler("help", help_command)
    start_handler = CommandHandler("start", start_command)
    message_handler = MessageHandler(
        filters.PHOTO | filters.Document.IMAGE, handle_message
    )

    application.add_handler(help_handler)
    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()
