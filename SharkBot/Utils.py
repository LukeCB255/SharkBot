import difflib
import io
import json
import os
import traceback
from datetime import timedelta, datetime
from typing import Optional, Union, Callable
import logging

import colorama
import discord
import humanize
from discord.ext import commands

import SharkBot

task_error_logger = logging.getLogger("task_error")

def get_dir_filepaths(directory: str, extension: Optional[str] = None) -> list[str]:
    """
    Returns a list of all files in the directory, including the path to the directory

    :param directory: Directory to be listed
    :param extension: (Optional) If defined, only files with this extension are returned
    :return: List of files in the directory including paths
    """
    if extension is None:
        return [f"{directory}/{filename}" for filename in os.listdir(directory)]
    else:
        if not extension.startswith("."):
            extension = f".{extension}"
        return [f"{directory}/{filename}" for filename in os.listdir(directory) if filename.endswith(extension)]

def command_usage(ctx: commands.Context) -> str:
    return f"{ctx.author.mention} used `{ctx.command}` in {ctx.channel} - `{ctx.message.content}`"

def time_it(func: Callable):
    def wrapper(*args, **kwargs):
        start = datetime.utcnow()
        func(*args, **kwargs)
        end = datetime.utcnow()
        print(f"{func.__name__} completed in {(end-start).total_seconds()}s")
    return wrapper

def split_embeds(embed: discord.Embed, split: str = "\n") -> list[discord.Embed]:
    fields = embed.fields
    embed.clear_fields()

    field_texts = []
    for field in fields:
        field_text = ""
        for line in field.value.split(split):
            if len(field_text + split + line) > 1000:
                field_texts.append((field.name, field_text[:-1], field.inline))
                field_text = ""
            field_text += f"{line}{split}"
        field_texts.append((field.name, field_text[:-1], field.inline))

    for name, value, inline in field_texts:
        if len(embed) + len(name) + len(value) > 5500 or len(embed.fields) == 25:
            yield embed
            embed.clear_fields()
        embed.add_field(
            name=name,
            value=value,
            inline=inline
        )
    yield embed


def get_similar_items(search: str, cutoff: float = 0.6, n: int = 1) -> Optional[str]:
    search = search.upper()
    result = difflib.get_close_matches(
        search,
        ([i.name.upper() for i in SharkBot.Item.items] + [i.id.upper() for i in SharkBot.Item.items]),
        n=n,
        cutoff=cutoff
    )
    return None if len(result) == 0 else result[0]


def get_similar_collections(search: str) -> Optional[str]:
    collections = SharkBot.Collection.collections
    result = difflib.get_close_matches(
        search,
        ([c.name.upper() for c in collections] + [c.id.upper() for c in collections]),
        n=1
    )
    return None if len(result) == 0 else result[0]


def get_similar_commands(bot: commands.Bot, search: str, cutoff: float = 0.6) -> Optional[str]:
    result = difflib.get_close_matches(
        search.lower(),
        [command.name for command in bot.commands],
        n=1,
        cutoff=cutoff
    )
    return None if len(result) == 0 else result[0]


def td_to_string(time_remaining: timedelta) -> str:
    return humanize.precisedelta(time_remaining, format="%0.0f")


async def task_loop_handler(bot: commands.Bot, error: Exception):

    error_type = type(error)
    error_name = f"{error_type.__module__}.{error_type.__name__}"

    dev = await bot.fetch_user(SharkBot.IDs.dev)
    embed = discord.Embed()
    embed.title = "Task Error Report"
    # description error traceback
    embed.description = f"```py\n{traceback.format_exc()}```"
    embed.add_field(name="Type", value=error_name, inline=False)
    await dev.send(embed=embed)
    task_error_logger.error(error, exc_info=True)
    raise error

class FileChecker:

    @classmethod
    def directory(cls, path: str):
        if not os.path.isdir(path):
            os.makedirs(path)
            print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + f"Created Directory: '{path}'")

    @classmethod
    def file(cls, path: str, default_value: str = ""):
        if not os.path.isfile(path):
            directory = os.path.split(path)[0]
            if directory != "":
                cls.directory(directory)
            with open(path, "w+") as outfile:
                outfile.write(default_value)
                print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + f"Created File: '{path}'")

    @classmethod
    def json(cls, path: str, default_value, indent: int = 2):
        if not os.path.isfile(path):
            directory = os.path.split(path)[0]
            if directory != "":
                cls.directory(directory)
            with open(path, "w+") as outfile:
                json.dump(default_value, outfile, indent=indent)
                print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + f"Created JSON: '{path}'")


class JSON:

    @staticmethod
    def load(filepath: str):
        with open(filepath, "r") as _infile:
            return json.load(_infile)

    @staticmethod
    def dump(filepath: str, data, indent: int = 2):
        try:
            with open(filepath, "w+") as _outfile:
                json.dump(data, _outfile, indent=indent)
        except FileNotFoundError:
            FileChecker.json(filepath, data)

    @staticmethod
    def dumps(data, indent: int = 2) -> str:
        return json.dumps(data, indent=indent)


class Embed:

    @staticmethod
    async def send(embed: discord.Embed, ctx: commands.Context) -> list[discord.Message]:
        messages = []
        for e in split_embeds(embed):
            messages.append(await ctx.send(embed=e))
        return messages

    @staticmethod
    async def send_with_replace(embed: discord.Embed, ctx: commands.Context, messages: list[discord.Message]) -> list[discord.Message]:
        _messages = []
        i = 0
        for i, e in enumerate(split_embeds(embed)):
            if i < len(messages):
                _messages.append(await messages[i].edit(embed=e))
            else:
                _messages.append(await ctx.send(embed=e))
        for message in messages[i+1:]:
            await message.delete()
        return _messages

    @staticmethod
    async def reply(embed: discord.Embed, message: Union[discord.Message, commands.Context], mention_author: bool = False) -> list[discord.Message]:
        messages = []
        for e in split_embeds(embed):
            messages.append(await message.reply(embed=e, mention_author=mention_author))
        return messages

    @staticmethod
    async def reply_with_replace(embed: discord.Embed, message: Union[discord.Message, commands.Context], messages: list[discord.Message], mention_author: bool = False) -> list[discord.Message]:
        _messages = []
        i = 0
        for i, e in enumerate(split_embeds(embed)):
            if i < len(messages):
                _messages.append(await messages[i].edit(embed=e))
            else:
                _messages.append(await message.reply(embed=e, mention_author=mention_author))
        for _message in messages[i+1:]:
            await _message.delete()
        return _messages

def item_contains(item, search: str) -> bool:
    return search in item.id.lower() or search in item.name.lower()


class Colours:

    class Text:
        @staticmethod
        def red(string: str) -> str:
            return colorama.Fore.RED + string

        @staticmethod
        def green(string: str) -> str:
            return colorama.Fore.GREEN + string

        @staticmethod
        def blue(string: str) -> str:
            return colorama.Fore.BLUE + string

        @staticmethod
        def black(string: str) -> str:
            return colorama.Fore.BLACK + string

        @staticmethod
        def yellow(string: str) -> str:
            return colorama.Fore.YELLOW + string

        @staticmethod
        def magenta(string: str) -> str:
            return colorama.Fore.MAGENTA + string

        @staticmethod
        def cyan(string: str) -> str:
            return colorama.Fore.CYAN + string

        @staticmethod
        def white(string: str) -> str:
            return colorama.Fore.WHITE + string

    class Back:
        @staticmethod
        def red(string: str) -> str:
            return colorama.Back.RED + string

        @staticmethod
        def green(string: str) -> str:
            return colorama.Back.GREEN + string

        @staticmethod
        def blue(string: str) -> str:
            return colorama.Back.BLUE + string

        @staticmethod
        def black(string: str) -> str:
            return colorama.Back.BLACK + string

        @staticmethod
        def yellow(string: str) -> str:
            return colorama.Back.YELLOW + string

        @staticmethod
        def magenta(string: str) -> str:
            return colorama.Back.MAGENTA + string

        @staticmethod
        def cyan(string: str) -> str:
            return colorama.Back.CYAN + string

        @staticmethod
        def white(string: str) -> str:
            return colorama.Back.WHITE + string

    red = Text.red
    green = Text.green
    blue = Text.blue
    black = Text.black
    yellow = Text.yellow
    magenta = Text.magenta
    cyan = Text.cyan
    white = Text.white

    @classmethod
    def bool_rg(cls, value: bool) -> str:
        colour = cls.green if value else cls.red
        return colour(str(value))