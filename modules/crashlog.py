import io

import discord
from discord.ext import commands
import re

thaumic_tinkerer_link = "https://github.com/Midnight145/ThaumicTinkerer/releases/latest"

filename_regex = r"^crash-\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}-(client|server)\.txt$"

crashes = {
    r"java\.lang\.OutOfMemoryError:":
        "You ran out of memory, allocate more RAM to Java.",

    r"java\.lang\.ArrayIndexOutOfBoundsException: -1[\n\r]+\s+at net\.minecraft\.client\.gui\.achievement"
    r"\.GuiStats\$StatsBlock\.<init>":
        "HQM breaks the achivements button, unfortunately there's not much you can do.",

    r"java.util.ConcurrentModificationException[\n\r]+\s+at java.util.HashMap\$HashIterator.nextNode":
        "**If** this happened while teleporting to the Jaded or doing a scan, it's possible your `scanner.dat` has "
        "become corrupted. Deleted it from saves/worldname, and it will be recreated on next scan.",

    r"java\.io\.EOFException: Unexpected end of ZLIB input stream":
        "Your `scanner.dat` file is most likely corrupted, delete it from saves/worldname.",

    r"Java VM Version: Java HotSpot\(TM\) (?!64-Bit).+Server VM \(mixed mode\), Oracle Corporation":
        "You are running a 32-bit version of Java. Install and select a 64 bit version.",

    r"java.lang.NullPointerException: Ticking memory connection[\r\n]+\s+at thaumic.tinkerer.common.item.foci."""
    r"ItemFocusDislocation.onFocusRightClick":
        "The version of Thaumic Tinkerer packaged in Blightfall has issues when trying to dislocate some certain "
        "blocks, which will cause a crash.",

    r"java.lang.IllegalArgumentException: bound must be positive[\r\n]+\s+at java.util.Random.nextInt.+[\r\n]+\s+at "
    "thaumic.tinkerer.common.core.helper.AspectCropLootManager.getLootForAspect":
        "The version of Thaumic Tinkerer packaged in Blightfall has some issues with specific types of infused seeds "
        "having invalid drops, causing a crash.",

    r"java.lang.NullPointerException: Ticking memory connection[\r\n]+\s+at thaumic.tinkerer.common.block."""
    r"BlockInfusedGrain.getDrops":
        "The version of Thaumic Tinkerer packaged in Blightfall has some issues with specific types of infused seeds "
        "having invalid drops, causing a crash.",

    r"cpw\.mods\.fml\.common\.DuplicateModsFoundException":
        "You have at least 1 duplicate mod in your mods folder. **IF** you installed Midnight's BlightBuster fork, "
        "make sure you deleted reqcredit-1.1.19.jar"
}


class Crashlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.attachments) == 1:
            attachment: discord.Attachment = message.attachments[0]
            if re.match(filename_regex, attachment.filename):
                tmp_file = io.BytesIO()
                await attachment.save(tmp_file)
                fstring = tmp_file.read().decode()

                found = False

                for check in crashes.keys():
                    if re.search(check, fstring):
                        found = True
                        await message.channel.send(crashes[check])
                if not found:
                    return


async def setup(bot):
    await bot.add_cog(Crashlog(bot))
