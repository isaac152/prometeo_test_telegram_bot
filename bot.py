
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode, message
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    Defaults,
    CallbackQueryHandler
)
from prometeus import get_providers,User,provider_info
from telegram_calendar.telegramcalendar import create_calendar,process_calendar_selection
from configure import TELEGRAM_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#Constants
LOGIN,COMMANDHELP,PROVIDER,USERNAME,PASSWORD = range(5)
ACCOUNT, DATES= range(2)

#Get the providers data
providers = get_providers()
providers_codes,providers_names = provider_info(providers)
providers= [p['name']+' '+p['country'] for p in providers]

def start(update: Update, context: CallbackContext) -> None:
    """Starts the conversation """
    reply_text = "Hi! I am the Prometeo Telegram Bot\n"
    if 'login' in context.user_data:
        reply_text += ("Its looks like you already login before, isnt it? Well let me help you")
        update.message.reply_text(reply_text)
        help_message(update,context)
    else:
        reply_text += ('Firs time huh?, Dont worry i will guide you\nPlease use /login')
        update.message.reply_text(reply_text)


def login(update:Update,context:CallbackContext)->int:
    """Login entry"""
    logger.info("login entry")
    update.message.reply_text(
        'First of all, you need to select a provider\n\n'
        'Btw, you can send /cancel to stop our little talk \n \n'
        'Please select your provider:',
        reply_markup=ReplyKeyboardMarkup([[i] for i in providers],one_time_keyboard=True, input_field_placeholder='Which provider?'),
    )
    return PROVIDER

def provider(update: Update, context: CallbackContext) -> int:
    """Save select provider"""
    user = update.message.from_user
    logger.info("Provider of %s: %s", user.first_name, update.message.text)
    context.user_data['login_data']={'provider':providers_codes[update.message.text]}
    update.message.reply_text(
        f'Thanks, now i need your username for {update.message.text}',
        reply_markup=ReplyKeyboardRemove(),
    )
    return USERNAME

def username(update: Update, context: CallbackContext) -> int:
    """Save the username"""
    user = update.message.from_user
    logger.info("username of %s: %s", user.first_name, update.message.text)
    context.user_data['login_data'].update({'username':update.message.text})
    update.message.reply_text(
        'Perfect, now i need the password please, dont worry i wont look '
    )
    return PASSWORD
    
def password(update: Update, context: CallbackContext) -> int:
    """Save the password"""
    user = update.message.from_user
    logger.info("password of %s: %s", user.first_name, update.message.text)
    context.user_data['login_data'].update({'password':update.message.text})
    context.bot.deleteMessage(message_id=update.message.message_id,chat_id=update.message.chat_id)
    update.message.reply_text(
        'Thanks, now let me check please'
    )
    return check_login(update,context)


def check_login(update:Update, context:CallbackContext)->int:
    """Check the data and create an user and then login"""
    user = update.message.from_user
    logger.info(f"User:{user} Data: {context.user_data['login_data']}")
    provider = context.user_data['login_data']['provider']
    prometeus_user = context.user_data.get('user_prometeus',User())
    prometeus_user.set_user_data(**context.user_data['login_data'])
    if not 'user_prometeus' in context.user_data:
        print(prometeus_user.user_data)
        context.user_data['user_prometeus']=prometeus_user
    if(prometeus_user.login(provider)):
        update.message.reply_text('Everything seems fine to me')
        context.user_data['login']=True    
    else:
        update.message.reply_text('Ups, maybe you had a typo?')
    del context.user_data['login_data']
    return ConversationHandler.END

def display_info(update:Update,context:CallbackContext)->int:
    """Display the info returned from the API"""
    user = context.user_data['user_prometeus']
    operation = context.user_data.get('operation','error')
    result= user.wrapper_operation(operation,providers_codes[update.message.text])
    del context.user_data['operation']
    for r in result:
        update.message.reply_text(r)
    return ConversationHandler.END

def general_operation(update:Update,context:CallbackContext)->None:
    """Select the provider to execute an operation from the API"""
    user = context.user_data['user_prometeus']
    providers_markup = [[providers_names[provider]] for provider in user.user_data.keys()]
    markup=ReplyKeyboardMarkup(providers_markup,one_time_keyboard=True,input_field_placeholder="Which provider?")
    update.message.reply_text(
        'You need to select a provider\n'
        'Btw, you can send /cancel to stop our little talk \n \n'
        'Please select your provider:',
        reply_markup=markup,)


def account(update:Update,context:CallbackContext)->int:
    """Selec the get account operation from the API"""
    logger.info(f"Data: {context.user_data.get('user_prometeus','None')}")
    if 'user_prometeus' in context.user_data:
        general_operation(update,context)
        context.user_data['operation']='account'
        return PROVIDER
    else:
        error(update,context)
        return ConversationHandler.END

def credit_cards(update:Update,context:CallbackContext)->int:
    """Selec the get credit cards operation from the API"""
    if 'user_prometeus' in context.user_data:
        general_operation(update,context)
        context.user_data['operation']='credit_cards'
        return PROVIDER
    else:
        error(update,context)
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! Have a nice day', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def logout(update:Update,context:CallbackContext)->None:
    """Logout and delete all the login data saved in the context"""
    if 'login' in context.user_data:
        update.message.reply_text('See you space cowboy')
        del context.user_data['login']
        del context.user_data['user_prometeus']
        print(context.user_data)
    else:
        error(update,context)

def error(update:Update,context:CallbackContext,message=None)->None:
    """Error message"""
    if(not message):
        update.message.reply_text("Sorry i can't do that, please /login first")
    else:
        update.message.reply_text(message)
def help_message(update:Update,context:CallbackContext)->None:
    """List of all commands"""
    logger.info(f"{context.user_data}")
    if 'login' in context.user_data:
        update.message.reply_text("Let me guide you a little bit")
        update.message.reply_text("/login if you want to add another bank-account")
        update.message.reply_text("/account if you... well... want to see the status of your bank-account")
        update.message.reply_text("/credit_cards check your credit cards")
        update.message.reply_text("/account_movements get the movements in a date range")
        update.message.reply_text("/logout if you want to exit from every account")
        update.message.reply_text("/help if you want to see this message again")
    else:
        update.message.reply_text("use /login to access others commands")

def account_movements(update:Update,context:CallbackContext)->int:
    """Selec the account_movements operation from the API"""
    logger.info(f"Data: {context.user_data.get('user_prometeus','None')}")
    if 'user_prometeus' in context.user_data:
        general_operation(update,context)
        return ACCOUNT
    else:
        error(update,context)
        return ConversationHandler.END
def select_account(update:Update,context:CallbackContext)->int:
    """Select the account you want to check"""
    user = context.user_data['user_prometeus']
    provider= providers_codes[update.message.text]
    accounts_provider = user.user_data[provider].get('accounts',None)
    if(accounts_provider):
        context.user_data['account_movements']={'provider':provider}
        account_markup = [[account] for account in accounts_provider.keys()]
        markup=ReplyKeyboardMarkup(account_markup,one_time_keyboard=True,input_field_placeholder="Which account?")
        update.message.reply_text(
            'You need to select an account \n'
            'Btw, you can send /cancel to stop our little talk \n \n'
            'Please select your account:',
            reply_markup=markup,)
        return DATES
    error(update,context,'Ups, you need to use /account at least one time, so i can know your accounts in this provider')
    return ConversationHandler.END

def select_date(update:Update,context:CallbackContext)->int:
    """Execute the inline_handler to select a date"""
    context.user_data['account_movements'].update({'account_name':update.message.text})
    update.message.reply_text('Select the date',reply_markup=create_calendar())
    return ConversationHandler.END

def inline_handler(update:Update, context:CallbackContext)->int:
    """Callbacks handler, for now only redirect to the inline_calendar handler"""
    query = update.callback_query
    (kind, _, _, _, _) = (query.data).split(';')
    if kind == "CALENDAR":
        return inline_calendar_handler(update, context)

def inline_calendar_handler(update:Update, context:CallbackContext)->int:
    """Manage the inline calendar logic"""
    selected,date = process_calendar_selection(update, context)
    if selected:
        text_date= date.strftime('%d/%m/%Y')
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
        text=text_date,reply_markup=ReplyKeyboardRemove())
        if('dates' not in context.user_data):
            context.user_data['dates']={'first':date}
            context.bot.send_message(chat_id=update.callback_query.from_user.id,
            text='Select another date: ',reply_markup=create_calendar())
        else:
            context.user_data['dates'].update({'second':date})
            return check_dates(update,context)


def check_dates(update:Update,context:CallbackContext)->int:
    """If dates are ok, call the operaton and return the results"""
    first_date = context.user_data['dates']['first']
    second_date = context.user_data['dates']['second']
    account_name = context.user_data['account_movements']['account_name']
    provider = context.user_data['account_movements']['provider']
    del context.user_data['dates']
    del context.user_data['account_movements']
    if(second_date>=first_date):
        user = context.user_data['user_prometeus']
        first_date = first_date.strftime("%d/%m/%Y")
        second_date = second_date.strftime("%d/%m/%Y")
        lista=user.wrapper_operation('account_movements',provider,account=account_name,first_date=first_date,second_date=second_date)
        for i in lista:
            context.bot.send_message(chat_id=update.callback_query.from_user.id,text=i)
    else:
        update.message.reply_text('Error in the dates')
    return ConversationHandler.END

def test(update:Update,context:CallbackContext)->None:
    """Just to add the test user without all the login process"""
    context.user_data['login_data']={
            'username':'12345',
            'password':'gfdsa',
            'provider':'test'
        }
    check_login(update,context)

def not_found(update: Update, context: CallbackContext)->None:
    """Message when user input a invalid command"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def main() -> None:
    """Run the bot."""
    defaults = Defaults(parse_mode=ParseMode.HTML)
    updater = Updater(TELEGRAM_KEY,defaults=defaults)
    dispatcher = updater.dispatcher
    test_command= CommandHandler('test',test)
    cancel_command = CommandHandler('cancel', cancel)
    logount_command = CommandHandler('logout', logout)
    login_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login)],
        states = {
            PROVIDER: [MessageHandler(Filters.text(providers),provider)],
            USERNAME: [MessageHandler(Filters.text & ~Filters.command, username)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, password)],
        },
        fallbacks=[cancel_command],
    )
    account_movement_command=ConversationHandler(
        entry_points=[CommandHandler('account_movements',account_movements)],
        states = {
            #PROVIDER: [MessageHandler(Filters.text(providers),display_info)],
            ACCOUNT : [MessageHandler(Filters.text & ~Filters.command, select_account)],
            DATES :[MessageHandler(Filters.all & ~Filters.command,select_date)],
            9:[MessageHandler(Filters.text,check_dates)]
        },
        fallbacks=[cancel_command]
    )
    start_command =CommandHandler('start', start)
    help_command =CommandHandler('help', help_message)
    account_command = ConversationHandler(
        entry_points=[CommandHandler('account',account)],
        states = {
            PROVIDER: [MessageHandler(Filters.text(providers),display_info)],
        },
        fallbacks=[cancel_command],
        )
    credit_cards_command = ConversationHandler(
        entry_points=[CommandHandler('credit_cards',credit_cards)],
        states = {
            PROVIDER: [MessageHandler(Filters.text(providers),display_info)],
        },
        fallbacks=[cancel_command]
    )
    unknown_handler = MessageHandler(Filters.command, not_found)
    dispatcher.add_handler(help_command)
    dispatcher.add_handler(start_command)
    dispatcher.add_handler(test_command)
    dispatcher.add_handler(CallbackQueryHandler(inline_handler))
    dispatcher.add_handler(login_handler)
    dispatcher.add_handler(logount_command)
    dispatcher.add_handler(account_movement_command)
    dispatcher.add_handler(account_command)
    dispatcher.add_handler(credit_cards_command)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()