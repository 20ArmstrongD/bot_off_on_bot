import discord
from discord.ext import commands
import os
import signal
import asyncio
from dotenv import load_dotenv

# Load the Discord bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Load intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

STALLIONS_ROLE = 'The Stallions'
MEMBER_ASSIGNMENT_ROLE = 'Member Assignment'

# Offline notification channel
OFFLINE_NOTIFICATION_CHANNEL = 'paddys-pub'

# Track online/offline notifications
online_stallions_sent = False
offline_stallions_sent = False
online_member_assignment_sent = False
offline_member_assignment_sent = False

# Announce when a user with a specific role is online or offline
@bot.event
async def on_presence_update(before, after):
    global online_stallions_sent, offline_stallions_sent
    global online_member_assignment_sent, offline_member_assignment_sent
    
    guild = after.guild
    channel = discord.utils.get(guild.channels, name=OFFLINE_NOTIFICATION_CHANNEL)

    # Get the specific roles
    stallions_role = discord.utils.get(guild.roles, name=STALLIONS_ROLE)
    member_assign_role = discord.utils.get(guild.roles, name=MEMBER_ASSIGNMENT_ROLE)

    # Check if the member has the required roles
    has_stallions_role = stallions_role in after.roles
    has_member_assign_role = member_assign_role in after.roles

    # Handle Stallions role
    if has_stallions_role:
        if before.status != after.status:  # Only act if the status has changed
            if after.status == discord.Status.online:
                if not online_stallions_sent:
                    await channel.send("🟢 Roles Online: `The Stallions` have bots online.")
                    online_stallions_sent = True
                offline_stallions_sent = False  # Reset the offline flag when a bot comes online
            elif after.status == discord.Status.offline:
                if not offline_stallions_sent:
                    await channel.send("🔴 Roles Offline: `The Stallions` have bots offline.")
                    offline_stallions_sent = True

    # Handle Member Assignment role
    if has_member_assign_role:
        if before.status != after.status:  # Only act if the status has changed
            if after.status == discord.Status.online:
                if not online_member_assignment_sent:
                    await channel.send("🟢 Roles Online: `Member Assignment` have bots online.")
                    online_member_assignment_sent = True
                offline_member_assignment_sent = False  # Reset the offline flag when a bot comes online
            elif after.status == discord.Status.offline:
                if not offline_member_assignment_sent:
                    await channel.send("🔴 Roles Offline: `Member Assignment` have bots offline.")
                    offline_member_assignment_sent = True

# Bot start message
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Function to check which bots with roles are online and send a shutdown message
async def send_shutdown_message():
    guild = discord.utils.get(bot.guilds)
    channel = discord.utils.get(guild.channels, name=OFFLINE_NOTIFICATION_CHANNEL)
    
    if channel:
        # Fetch all members in the guild
        members = await guild.fetch_members().flatten()
        
        # Prepare the message to send about bots going offline
        bots_going_offline = []

        # Check which bots are online and have the Stallions or Member Assign roles
        for member in members:
            if member.bot:  # Check if the member is a bot
                stallions_role = discord.utils.get(guild.roles, name=STALLIONS_ROLE)
                member_assign_role = discord.utils.get(guild.roles, name=MEMBER_ASSIGNMENT_ROLE)

                # Check if the bot has any of the tracked roles and is online
                if (stallions_role in member.roles or member_assign_role in member.roles) and member.status != discord.Status.offline:
                    bots_going_offline.append(member.name)

        # Send message listing bots going offline
        if bots_going_offline:
            bots_message = "⚠️ The following bots are going offline: " + ", ".join(bots_going_offline)
        else:
            bots_message = "⚠️ No tracked bots are currently online."

        await channel.send(bots_message)

# Handle graceful shutdown by listening for termination signals
def shutdown_handler(*args):
    loop = asyncio.get_event_loop()
    loop.create_task(send_shutdown_message())
    loop.run_until_complete(asyncio.sleep(2))  # Give it time to send the message
    bot.close()

# Capture signals like SIGINT (CTRL+C) or SIGTERM (termination signal)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Run the bot
print(f"logged in as {TOKEN}")
bot.run(TOKEN)
