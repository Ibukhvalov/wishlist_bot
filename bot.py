import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN
from keyboards import main_actions_kb

from db import init_db, get_all_items, get_comments_for_gift, add_item, reserve_gift, unreserve_gift, update_comment, delete_comment, get_reserved_by

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🎁 Welcome to the Birthday Wishlist Bot!\n\n"
        "Use /list to see gifts\n"
        "Use /add to add a new gift\n"
        "Use /comment to comment on a gift\n"
        "Use /reserve to reserve a gift\n"
        "Use /unreserve to unreserve a gift\n"
    )

@dp.message(Command("list"))
async def list_handler(message: Message):
    items = get_all_items()

    if not items:
        await message.answer("🎁 Wishlist is empty… for now 👀",
            reply_markup=main_actions_kb())
        return

    lines = ["🎂🎁 *Birthday Wishlist* 🎁🎂\n"]

    for item in items:
        status = item["status"]

        status_line = {
            "available": "🟢 *Available*",
            "commented": "🟡 *Commented*",
            "reserved": f"🔴 *Reserved* by *@{item['reserved_by']}*"
        }.get(status, status) or status

        lines.append(f"{item['id']}️⃣ *{item['title']}*")
        if item["description"]:
            lines.append(f"_{item['description']}_")

        lines.append(status_line)

        comments = get_comments_for_gift(item["id"])
        if comments:
            lines.append("\n💬 *Comments:*")
            for c in comments:
                lines.append(f"👤 {c['author']}: _{c['text']}_")

        lines.append("\n──────────────\n")

    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_actions_kb()
    )

class AddGift(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


@dp.message(Command("add"))
async def add_start(message: Message, state: FSMContext):
    await message.answer(
        "🎁 Let’s add a new gift!\n\n"
        "Send me a *short title* 👇\n",
        parse_mode="Markdown"
    )
    await state.set_state(AddGift.waiting_for_title)

@dp.message(AddGift.waiting_for_title)
async def add_get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)

    await message.answer(
        "✍️ Nice!\n"
        "Now send a *description* (or `-` if not needed)\n\n",
        parse_mode="Markdown"
    )
    await state.set_state(AddGift.waiting_for_description)

@dp.message(AddGift.waiting_for_description)
async def add_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    title: str = data["title"]
    description = (
        None if str(message.text).strip() == "-" else message.text
    )

    assert message.from_user
    gift_id = add_item(title, description, str(message.from_user.username))

    await message.answer(
        "✅ *Gift added!*\n\n"
        f"{gift_id}️⃣ *{title}*\n"
        f"{f'_{description}_' if description else ''}\n\n"
        "Let the birthday magic begin 🎂✨",
        parse_mode="Markdown",
        reply_markup=main_actions_kb()
    )

    await state.clear()

class AddComment(StatesGroup):
    waiting_for_gift_id = State()
    waiting_for_text = State()

@dp.message(Command("comment"))
async def comment_start(message: Message, state: FSMContext):
    await message.answer(
        "💬 Which gift do you want to comment on?\n"
        "Send the *gift number* 👇",
        parse_mode="Markdown"
    )
    await state.set_state(AddComment.waiting_for_gift_id)



@dp.message(AddComment.waiting_for_gift_id)
async def comment_get_id(message: Message, state: FSMContext):
    if not str(message.text).isdigit():
        await message.answer("❌ Please send a number 🙃")
        return

    gift_id = int(str(message.text))

    await state.update_data(gift_id=gift_id)

    await message.answer(
        "✍️ Now send your comment\n",
        parse_mode="Markdown"
    )
    await state.set_state(AddComment.waiting_for_text)

@dp.message(AddComment.waiting_for_text)
async def comment_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    gift_id: int = data["gift_id"]

    user = message.from_user
    assert user is not None
    author = (
        f"@{user.username}"
        if user.username
        else user.full_name
    )

    from db import add_comment
    add_comment(gift_id, author, str(message.text))

    await message.answer(
        "✅ Comment added!\n"
        "Thanks for coordinating like a legend 🎉",
        reply_markup=main_actions_kb()
    )

    await state.clear()

class ReserveGift(StatesGroup):
    waiting_for_id = State()

@dp.message(Command("reserve"))
async def reserve_start(message: Message, state: FSMContext):
    await message.answer("🔒 Send gift number to reserve 👇")
    await state.set_state(ReserveGift.waiting_for_id)


@dp.message(ReserveGift.waiting_for_id)
async def reserve_finish(message: Message, state: FSMContext):
    if not str(message.text).isdigit():
        await message.answer("❌ Number please 🙂")
        return

    gift_id = int(str(message.text))
    assert message.from_user is not None
    user = message.from_user.username or message.from_user.full_name

    reserve_gift(gift_id, user)

    await message.answer(
        "🔒 Gift reserved! No duplicates today 😎",
        reply_markup=main_actions_kb()
    )
    await state.clear()

class UnreserveGift(StatesGroup):
    waiting_for_id = State()

@dp.message(Command("unreserve"))
async def unreserve_start(message: Message, state: FSMContext):
    await message.answer("🔓 Send gift number to unreserve 👇")
    await state.set_state(UnreserveGift.waiting_for_id)

@dp.message(UnreserveGift.waiting_for_id)
async def unreserve_finish(message: Message, state: FSMContext):
    if not str(message.text).isdigit():
        await message.answer("❌ Please send a number 🙃")
        return

    gift_id = int(str(message.text))
    assert message.from_user
    user = message.from_user.username or message.from_user.full_name

    # Check current reservation
    reserved_by_author = get_reserved_by(gift_id)
    if(reserved_by_author is None):
        await message.answer("❌ Gift not found.")
        await state.clear()
        return

    author = reserved_by_author[0]
    if(author != user):
        print(author, user)
        await message.answer("❌ You can only unreserve gifts you reserved.")
        await state.clear()
        return

    unreserve_gift(gift_id)
    await message.answer(
        "🔓 Gift is free again 🎁",
        reply_markup=main_actions_kb()
    )
class RemoveComment(StatesGroup):
    waiting_for_comment_id = State()

@dp.message(Command("uncomment"))
async def uncomment_start(message: Message, state: FSMContext):
    await message.answer("🗑 Send *comment ID* to remove", parse_mode="Markdown")
    await state.set_state(RemoveComment.waiting_for_comment_id)

@dp.message(RemoveComment.waiting_for_comment_id)
async def uncomment_finish(message: Message, state: FSMContext):
    if not str(message.text).isdigit():
        return

    assert message.from_user is not None
    author = message.from_user.username or message.from_user.full_name
    delete_comment(int(str(message.text)), author)

    await message.answer(
        "🗑 Comment removed.",
        reply_markup=main_actions_kb()
    )
    await state.clear()

@dp.callback_query(lambda c: c.data == "list")
async def show_list(call: CallbackQuery):
    await list_handler(call.message)
    await call.answer()  # stops the loading animation

@dp.callback_query(lambda c: c.data == "comment")
async def start_comment(call: CallbackQuery, state: FSMContext):
    await comment_start(call.message, state)
    await call.answer()

@dp.callback_query(lambda c: c.data == "add")
async def start_comment(call: CallbackQuery, state: FSMContext):
    await add_start(call.message, state)
    await call.answer()

@dp.callback_query(lambda c: c.data == "reserve")
async def start_reserve(call: CallbackQuery, state: FSMContext):
    await reserve_start(call.message, state)
    await call.answer()

@dp.callback_query(lambda c: c.data == "unreserve")
async def start_unreserve(call: CallbackQuery, state: FSMContext):
    await unreserve_start(call.message, state)
    await call.answer()
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_db()
    asyncio.run(main())
