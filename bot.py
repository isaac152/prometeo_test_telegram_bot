
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    Defaults
)
from prometeus import get_providers,User,provider_info

TELEGRAM_KEY="There's no dark side of the moon really."

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#Constants
LOGIN,COMMANDHELP,PROVIDER,USERNAME,PASSWORD = range(5)

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
        'First of all, you need to select a provider\n'
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
    for r in result:
        update.message.reply_text(r)

def general_operation(update:Update,context:CallbackContext)->None:
    """Select the provider to execute an operation from the API"""
    user = context.user_data['user_prometeus']
    providers_markup = [[providers_names[provider]] for provider in user.user_data.keys()]
    markup=ReplyKeyboardMarkup(providers_markup,one_time_keyboard=True,input_field_placeholder="Which provider?")
    update.message.reply_text(
        'You need to select a provider'
        'Btw, you can send /cancel to stop our little talk \n \n'
        'Please select your provider:',
        reply_markup=markup,)


def account(update:Update,context:CallbackContext)->int:
    """Selec the get account operation from the API"""
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
    else:
        error(update,context)

def error(update:Update,context:CallbackContext)->None:
    """Error message"""
    update.message.reply_text("Sorry i can't do that, please /login first")

def help_message(update:Update,context:CallbackContext)->None:
    """List of all commands"""
    logger.info(f"{context.user_data}")
    if 'login' in context.user_data:
        update.message.reply_text("Let me guide you a little bit")
        update.message.reply_text("/login if you want to add another bank-account")
        update.message.reply_text("/account if you... wel... want to see the status of your bank-account")
        update.message.reply_text("/credit_cards check your credit cards")
        update.message.reply_text("/logout if you want to exit from every account")
        update.message.reply_text("/help if you want to see this message again")
    else:
        update.message.reply_text("use /login to access others commands")

def main() -> None:
    """Run the bot."""
    defaults = Defaults(parse_mode=ParseMode.HTML)
    updater = Updater(TELEGRAM_KEY,defaults=defaults)
    dispatcher = updater.dispatcher
    
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

    dispatcher.add_handler(help_command)
    dispatcher.add_handler(start_command)
    dispatcher.add_handler(login_handler)
    dispatcher.add_handler(logount_command)
    dispatcher.add_handler(account_command)
    dispatcher.add_handler(credit_cards_command)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()