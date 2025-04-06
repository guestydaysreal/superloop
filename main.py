import discord
import requests
import asyncio
import time
import os
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# API URL
API_URL = "https://guestydaysreal.pythonanywhere.com/super?detail=true&image=true&judgement=true"

# Your channel ID where the bot will send messages
CHANNEL_ID = 1358464058860245054  # Replace with your Discord channel ID

# Store previous JSON data & last sent messages
previous_data = None
last_messages = []  # List to store sent messages

# Intents to allow reading messages
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
client = discord.Client(intents=intents)


async def fetch_last_bot_messages(channel):
    """Find the last messages sent by the bot."""
    messages = []
    async for message in channel.history(limit=20):  # Adjust limit if needed
        if message.author == client.user:
            messages.append(message)
    return messages[::-1]  # Reverse to maintain order


async def fetch_and_update():
    global previous_data, last_messages

    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print(f"❌ Error: Could not find channel {CHANNEL_ID}. Check the ID.")
        return

    # Get last bot messages after restart
    last_messages = await fetch_last_bot_messages(channel)

    while True:
        try:
            # Fetch JSON data
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()  # Ensure request didn't fail
            data = response.json()

            # Compare with previous data
            if data == previous_data:
                print("✅ No changes detected. Skipping update.")
            else:
                print("🔄 Changes detected! Updating Discord messages.")

                # Prepare embeds in batches of 10
                embeds = []
                for key, values in data.items():
                    name, variant, region, time_ago, image_url = values
                    embed = discord.Embed(
                        title=name, color=0x2bffa3  # Greenish color
                    )
                    embed.add_field(name="Variant", value=variant, inline=True)
                    embed.add_field(name="Region", value=region, inline=True)
                    embed.add_field(name="Time", value=time_ago, inline=False)
                    embed.set_thumbnail(url=image_url)
                    embeds.append(embed)

                embed_batches = [embeds[i:i + 10]
                                 for i in range(0, len(embeds), 10)]

                # Ensure we have enough messages to edit
                while len(last_messages) < len(embed_batches):
                    # Placeholder
                    new_message = await channel.send("🔄 Updating messages...")
                    last_messages.append(new_message)

                # Update messages
                for i, batch in enumerate(embed_batches):
                    content = (
                        f"# Super mobs alive (Update: <t:{round(time.time())}>)\n"
                        f"-# Made by <@1053298522612568155> (guestydays)"
                    )
                    try:
                        await last_messages[i].edit(content=content, embeds=batch)
                    except discord.errors.NotFound:
                        last_messages[i] = await channel.send(content=content, embeds=batch)

                # Delete excess messages if needed
                if len(last_messages) > len(embed_batches):
                    for msg in last_messages[len(embed_batches):]:
                        await msg.delete()
                    last_messages = last_messages[:len(embed_batches)]

                # Update previous data reference
                previous_data = data

        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Error: {e}")

        except discord.errors.HTTPException as e:
            print(f"❌ Discord API Error: {e}")

        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

        # Wait before next update
        await asyncio.sleep(10)


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    client.loop.create_task(fetch_and_update())


# Run the bot
client.run(BOT_TOKEN)
