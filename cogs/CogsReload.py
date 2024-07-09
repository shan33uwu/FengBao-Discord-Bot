import discord
from discord import app_commands
from discord.ext import commands
import os
from typing import Any

class CogsReload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload", description="重新載入所有 cog")
    async def reload(self, interaction: Any):
        # 檢查是否為機器人擁有者
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message("只有機器人擁有者可以使用此命令!", ephemeral=True)
            return

        # 先發送一個延遲回應
        await interaction.response.defer(ephemeral=True)

        # 重新載入所有 cog
        loaded_cogs = 0
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.bot.reload_extension(f"cogs.{filename[:-3]}")
                    loaded_cogs += 1
                except Exception as e:
                    print(f"無法重新載入 {filename}: {e}")

        try:
            # 同步指令樹
            await self.bot.tree.sync()

            # 計算已載入的指令數量
            loaded_commands = len(self.bot.tree.get_commands())

            # 使用 followup 發送消息
            await interaction.followup.send("已重新載入所有 cog 和指令。", ephemeral=True)
            await interaction.user.send(f"重新載入完成！已載入 {loaded_cogs} 個 cog 文件和 {loaded_commands} 個指令。")
        except discord.errors.HTTPException as e:
            print(f"發送消息時發生錯誤: {e}")
            try:
                await interaction.user.send(f"重新載入過程中發生錯誤,但已載入 {loaded_cogs} 個 cog 文件和 {loaded_commands} 個指令。")
            except:
                print("無法向使用者發送私訊。")
        except Exception as e:
            print(f"執行過程中發生未知錯誤: {e}")

async def setup(bot):
    await bot.add_cog(CogsReload(bot))