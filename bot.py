import discord
import openai
import re

from discord import option

bot = discord.Bot()

OPENAI_API_KEY = 'sk-...<secret>'
DISCORD_BOT_KEY = 'MT...<secret>'
SERVER_IDS = [1098765432198765432]

openai.api_key = OPENAI_API_KEY

history = dict()


def add_history(user: str, text: str, bot_answer: str):
    if not user in history:
        history[user] = []
    pair = dict(
        prompt=text,
        answer=bot_answer
    )
    history[user] = history[user][-9:] + [pair]

def get_history(user: str) -> list:
    if not user in history:
        return []
    return history[user]


def prompt_to_chat(user: str, prompt: str) -> str:
    previous = get_history(user)
    conversation = ""
    for chat in previous:
        conversation += f"Human: {chat['prompt']}\n" \
                        f"Bot: {chat['answer']}\n"
    return conversation + "\n" + f"Human: {prompt}"


def clean_bot_answer(answer: str) -> str:
    answer = answer.strip()
    answer = re.sub(r"^[a-zA-Z+]: ", "", answer)
    return answer


def chat_with_gpt(user: str, prompt: str, max_tokens: int = 100) -> str:
    print('prompt:', prompt)
    prompt_as_chat = prompt_to_chat(user, prompt)
    print('prompt_as_chat:', prompt_as_chat)
    bot_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_as_chat,
        max_tokens=max_tokens,
        temperature=0.25
    )
    print('bot response:', bot_response)
    bot_answer = '\n'.join([clean_bot_answer(choice.text) for choice in bot_response.choices])
    add_history(user, prompt, bot_answer)
    return bot_answer


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print(f"{bot.user.name} connected.")


@bot.event
async def on_message(message):
    # print(message)

    user = message.author
    if user == bot.user:
        return

    text = message.content
    if text.startswith('!chat '):
        prompt = text[6:]
        bot_answer = chat_with_gpt(user, prompt)
        await message.channel.send(f"> Your prompt is: {prompt}\nAnswer: {bot_answer}")


@bot.slash_command(guild_ids=SERVER_IDS)
@option(
    name="prompt",
    type=str,
    description="프롬프트를 적어주세요."
)
@option(
    name="max_length",
    type=int,
    description="AI가 출력할 수 있는 최대 답변 길이. (기본값: 100)",
    required=False,
)
async def chat(context, prompt: str, max_length: int):
    await context.defer()
    user = context.author
    bot_answer = chat_with_gpt(user, prompt, max_tokens=max_length or 100)
    await context.respond(f"> Prompt: {prompt}\n{bot_answer}")


def summarize_prompt(prompt: str):
    bot_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt + "\nSummarize sentence under 2000 lengths:",
        max_tokens=3000,
        temperature=0.0
    )
    return '\n'.join([choice.text for choice in bot_response.choices])


def create_image_embed(title: str, description: str, url: str):
    embed = discord.Embed(
        title=title,
        description=description,
    )
    embed.set_thumbnail(url=url)
    embed.set_image(url=url)
    return embed


@bot.slash_command(guild_ids=SERVER_IDS)
@option(
    name="prompt",
    type=str,
    description="생성하고 싶은 이미지를 묘사해주세요."
)
@option(
    name="n",
    type=int,
    description="생성하고자 하는 이미지의 개수 (기본값: 1)",
    required=False,
)
@option(
    name="size",
    type=str,
    description="이미지 크기. 반드시 `256x256`, `512x512`, or `1024x1024` 중 하나." \
                "(기본값: 256x256)",
    required=False,
)
async def image(context, prompt: str, n: int, size: str):
    await context.defer()
    print("Image prompt:", prompt)
    response = openai.Image.create(
        prompt=prompt,
        n=n or 1,
        size=size or "256x256"
    )
    data: list = response['data']
    for index, image in enumerate(data):
        title = f"Image generated #{index+1}"
        embed = create_image_embed(title, prompt, image['url'])
        await context.send('', embed=embed)
    await context.respond(f"> Prompt: {prompt}")


bot.run(DISCORD_BOT_KEY)

