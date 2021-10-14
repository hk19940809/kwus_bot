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

# bot起動時のイベントハンドラ
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-----')
    load_sheet()

def load_sheet():
    global REPLY
    REPLY = request_sheet_api(auth_google_api())

def auth_google_api():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = os.environ["GOOGLE_API_SECRET"]
            scopes = os.environ["GOOGLE_API_SCOPES"]
            flow = InstalledAppFlow.from_client_secrets_file(secret, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def request_sheet_api(creds):

    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
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

# メッセージ入力時のイベントハンドラ
@bot.event
async def on_message(message):

    c = message.content
    print(c)

    # メッセージ削除処理
    if c.startswith(command_prefix):
        await message.delete()

    if not REPLY: return
    for row in REPLY:
        if len(row) < 2:
            continue
        if row[1] in c:
            await message.channel.send(row[0])
            return

    await bot.process_commands(message)

# !reloadコマンド
@bot.command()
async def reload(ctx):
    """シートの内容をリロードします。"""
    preload = os.environ["PRELOAD_MESSAGE"]
    await ctx.send(preload)
    load_sheet()
    postload = os.environ["POSTLOAD_MESSAGE"]
    await ctx.send(postload)

# !byeコマンド
@bot.command()
async def bye(ctx):
    """botをログアウトさせます。"""
    exit_message = os.environ["EXIT_MESSAGE"]
    await ctx.send(exit_message)
    # スクリプト終了
    await bot.close()

# if __name__ == '__main__':
bot.run(os.environ['DISCORD_ACCESS_TOKEN'])
