import discord
from discord import app_commands
from discord.ext import commands

class Helps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="顯示所有可用的指令")
    async def help(self, interaction: discord.Interaction):
        help_embed = discord.Embed(title="機器人幫助", description="以下是可用的指令:", color=discord.Color.blue())

        # 獲取所有的 slash commands
        for command in self.bot.tree.get_commands():
            if not getattr(command, 'hidden', False):  # 如果命令沒有 hidden 屬性或 hidden 為 False
                name = command.name
                description = command.description if command.description else "無說明"
                help_embed.add_field(name=f"/{name}", value=description, inline=False)

        await interaction.response.send_message(embed=help_embed)

    help.hidden = True
        
async def setup(bot):
    await bot.add_cog(Helps(bot))
