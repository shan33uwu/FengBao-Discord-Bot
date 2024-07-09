import discord
from discord.ext import commands
import os

# 讀取 token.txt 中的 token
with open('token.txt', 'r') as f:
    TOKEN = f.read().strip()

# 創建 bot 實例
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 載入 cog
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                print(f"正在嘗試加載 {filename}")
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"成功加載 {filename}")
            except Exception as e:
                print(f"加載 {filename} 時出錯: {e}")

@bot.event
async def on_ready():
    try:
        print(f'{bot.user} 已經上線了!')
        
        # 同步命令樹
        try:
            await bot.tree.sync()
            print("命令樹已同步")
        except Exception as e:
            print(f"同步命令樹時出錯: {e}")
        
        # 獲取擁有者信息
        try:
            app_info = await bot.application_info()
            owner = app_info.owner
            print(f"機器人擁有者: {owner}")
        except Exception as e:
            print(f"獲取應用信息時出錯: {e}")
            return
        
        # 計算加載的 cog 和命令數量
        loaded_cogs = len(bot.cogs)
        loaded_commands = len(bot.tree.get_commands())
        print(f"已加載 {loaded_cogs} 個 cog 文件和 {loaded_commands} 個指令")
        
        # 嘗試發送私訊給擁有者
        try:
            await owner.send(f"機器人已啟動！已加載 {loaded_cogs} 個 cog 文件和 {loaded_commands} 個指令。")
            print("已成功發送私訊給擁有者")
        except Exception as e:
            print(f"發送私訊給擁有者時出錯: {e}")
    
    except Exception as e:
        print(f"on_ready 事件處理中發生錯誤: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith('https://') and 'discord.com/channels' in message.content:
        link_parts = message.content.split('/')
        server_id = int(link_parts[-3])
        channel_id = int(link_parts[-2])
        message_id = int(link_parts[-1])
        guild = bot.get_guild(server_id)
        channel = guild.get_channel(channel_id)
        linked_message = await channel.fetch_message(message_id)
        embed_color = linked_message.author.top_role.color
        if linked_message.content:
            embed = discord.Embed(color=embed_color, description=linked_message.content)
            embed.set_author(name=linked_message.author.display_name,
                             url=linked_message.jump_url,
                             icon_url=linked_message.author.display_avatar.url)
            await message.channel.send(f"**{linked_message.author.mention}** 在 <t:{int(linked_message.created_at.timestamp())}:F> 於 {linked_message.channel.mention} 發送了以下訊息:", embed=embed,silent = True,allowed_mentions=discord.AllowedMentions.none())
        if linked_message.embeds:
            await asyncio.sleep(0.5)
            for original_embed in linked_message.embeds:
                await message.channel.send(embed=original_embed)

# 運行 bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
