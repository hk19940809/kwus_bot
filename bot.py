from __future__ import print_function
from dotenv import load_dotenv
import os.path
import pickle
from discord.ext import commands
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


REPLY = []
load_dotenv()
command_prefix = os.environ["COMMAND_PREFIX"]
bot = commands.Bot(command_prefix=command_prefix)

# event handler when bot run
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-----')

# event handler when member sent message
@bot.event
async def on_message(message):

    c = message.content
    print(c)

    # delete message when message includes command prefix
    if c.startswith(command_prefix):
        await message.delete()

    if REPLY:
        for row in REPLY:
            if len(row) < 2:
                continue
            if row[1] in c:
                await message.channel.send(row[0])
                return

    await bot.process_commands(message)

# init command
@bot.command()
async def init(ctx):
    await load_sheet(ctx)

async def load_sheet(ctx):
    global REPLY
    creds = await auth_google_api(ctx)
    REPLY = request_sheet_api(creds)

async def auth_google_api(ctx):
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = os.environ["GOOGLE_API_SECRET"]
            scopes = os.environ["GOOGLE_API_SCOPES"]
            flow = InstalledAppFlow.from_client_secrets_file(secret, scopes=scopes, redirect_uri="http://localhost")
            message = await ctx.send(flow.authorization_url()[0])
            creds = flow.run_local_server()
            message.delete()
        # save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def request_sheet_api(creds):

    service = build('sheets', 'v4', credentials=creds)
    # call the Sheets API
    sheet = service.spreadsheets()
    valueRanges = get_value_ranges(sheet, get_ranges(sheet))

    result = []
    for vr in valueRanges:
        values = vr.get('values')
        for v in values:
            result.append(v)
            
    return result

def get_ranges(sheet):
    sheet_id = os.environ["SPREADSHEET_ID"]
    result = sheet.get(spreadsheetId=sheet_id).execute()
    sheets = result.get('sheets', [])
    ranges = []
    for s in sheets:
        title = s.get('properties').get('title')
        sheet_range = os.environ["SPREADSHEET_RANGE"]
        ranges.append(title+sheet_range)
    return ranges

def get_value_ranges(sheet, ranges):
    sheet_id = os.environ["SPREADSHEET_ID"]
    result = sheet.values().batchGet(spreadsheetId=sheet_id, ranges=ranges).execute()
    return result.get('valueRanges', [])

# reload command
@bot.command()
async def reload(ctx):
    """シートの内容をリロードします。"""
    preload = os.environ["PRELOAD_MESSAGE"]
    await ctx.send(preload)
    await load_sheet(ctx)
    postload = os.environ["POSTLOAD_MESSAGE"]
    await ctx.send(postload)

# sheet command
@bot.command()
async def sheet(ctx):
    """シートのURLを表示します。"""
    sheet_id = os.environ["SPREADSHEET_ID"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/"
    await ctx.send(url)

# bye command
@bot.command()
async def bye(ctx):
    """botをログアウトさせます。"""
    exit_message = os.environ["EXIT_MESSAGE"]
    await ctx.send(exit_message)
    await bot.close()

# if __name__ == '__main__':
bot.run(os.environ['DISCORD_ACCESS_TOKEN'])
