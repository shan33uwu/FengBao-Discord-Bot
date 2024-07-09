import discord
from discord import app_commands
from discord.ext import commands

class invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invite", description="顯示機器人邀請連結")
    async def invite(self, interaction: discord.Interaction):
        embed = discord.Embed(title="歡迎使用風暴機器人，這是我們的邀請連結", description="[點我邀請風暴機器人](https://discord.com/oauth2/authorize?client_id=1242816972304158820)\n[點我進入官方伺服器](https://discord.gg/daFQhVFGKj)", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(invite(bot))
